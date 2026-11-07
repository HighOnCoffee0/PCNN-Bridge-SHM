"""
Bridge SHM Physics-Constrained Neural Network (PCNN) — training script.

Key features
  1. Physics-constrained loss: learnable physics constants (warm-started from
     physics_coefficients.json) with algebraic tension / strain residuals.
  2. Monte Carlo Dropout: dropout stays active at inference; T stochastic
     passes give a predictive mean, std and 95% interval for every head.
  3. Graded Health Probabilities: SHI is binned into health grades and each
     MC pass votes for a grade -> P(Poor / Fair / Good) per sample.
  4. Weighted Loss Functions:
       a) per-sample weights (rare health grades + heavy-load events) on the
          train split only, and
       b) per-term weights: learned (homoscedastic) or fixed lambdas.

Training-quality graphs (new)
  Every epoch is recorded (not only every 10th) and saved to
  <RUN_NAME>_training_history.csv. At the end of the run these PNG graphs are
  saved beside the script, each with labelled axes:
    <RUN_NAME>_plot_1_training_loss.png      total training loss per epoch
    <RUN_NAME>_plot_2_loss_terms.png         each loss term per epoch (log scale)
    <RUN_NAME>_plot_3_validation_score.png   checkpoint-selection score per epoch
    <RUN_NAME>_plot_4_rmse_train_vs_val.png  train vs validation RMSE per output
    <RUN_NAME>_plot_5_physics_constants.png  the six learnable constants per epoch
    <RUN_NAME>_plot_6_test_fit.png           test: predicted vs true + error histograms
    <RUN_NAME>_plot_7_mc_calibration.png     MC Dropout interval coverage / spread
    <RUN_NAME>_plot_8_grade_confusion.png    test: true vs predicted health grade
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

try:  # plotting is optional: training still runs (and history is saved) without it
    import matplotlib
    matplotlib.use("Agg")  # draw to files only; no window needed
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
except ImportError:
    plt = None

SEED = 3408
torch.manual_seed(SEED)
np.random.seed(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using", DEVICE)

DATA_DIR = r"" #Input your path here (/data)
TRAIN_CSV = os.path.join(DATA_DIR, "train.csv")
VAL_CSV = os.path.join(DATA_DIR, "val.csv")
TEST_CSV = os.path.join(DATA_DIR, "test.csv")

# All outputs (checkpoint, predictions, log, metrics) are saved in the SAME
# folder as this script. Change RUN_NAME for every experiment; it is added to
# the start of each file name so runs never overwrite each other.
RUN_NAME = "runA"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def out_path(name):
    return os.path.join(OUT_DIR, f"{RUN_NAME}_{name}")


class _Tee:
    """Everything printed is also written to <RUN_NAME>_run_log.txt."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for st in self.streams:
            st.write(text)

    def flush(self):
        for st in self.streams:
            st.flush()


sys.stdout = _Tee(sys.__stdout__, open(out_path("run_log.txt"), "w", encoding="utf-8"))
print("Results will be saved to:", OUT_DIR, "| file prefix:", RUN_NAME + "_")

# Monte Carlo Dropout
DROPOUT_P = 0.1
MC_SAMPLES = 50

# Number of training epochs. 
EPOCHS = 70

# Health Grades
HEALTH_LABELS = ["Poor", "Fair", "Good"]
HEALTH_EDGES = torch.tensor([0.75, 0.85])  # <0.75, 0.75-0.85, >=0.85
N_GRADES = len(HEALTH_LABELS)

# Weighted loss — per-sample weights (train split only)
GRADE_WEIGHT_BETA = 0.5   # 0 = no class balancing, 1 = full inverse-frequency
GRADE_WEIGHT_MAX = 5.0    # cap on the grade weight
LOAD_ALPHA = 0.5          # extra weight for heavy loads: 1 + alpha * clamp(load_z, 0, LOAD_CAP)
LOAD_CAP = 3.0

# Weighted loss — per-term weights
# "uncertainty": learned homoscedastic weights (Kendall et al.)
# "fixed":       manual lambdas below
LOSS_MODE = "fixed"
FIXED_LAMBDAS = {            # order: data_strain, data_tension, data_shi, phys_strain, phys_tension
    "data_strain": 1.0, "data_tension": 1.0, "data_shi": 1.0,
    "phys_strain": 0.1, "phys_tension": 0.1,
}

# Normalization constants derived from the training split only (leak-free).
STATS = {
    "Vehicle_Load_tons": {"mean": 17.957643548559723, "std": 10.470587482442049},
    "Temperature_C": {"mean": 16.791843608424514, "std": 7.5882118881340554},
    "Vibration_ms2": {"mean": 1.3447699137276217, "std": 0.9940116030681987},
    "Strain_microstrain": {"mean": 852.4109690413213, "std": 351.7855302575076},
    "Cable_Member_Tension_kN": {"mean": 476.2625261214879, "std": 91.63985725087804},
    "Structural_Health_Index_SHI": {"mean": 0.8162494171771701, "std": 0.05255583202133257},
}

PHYSICS_INIT = {
    "k_hat": 8.580678093067355,
    "b1_hat": 322.1737675212626,
    "c1_hat": 0.8618811649899571,
    "c2_hat": 0.5680792020564921,
    "c3_hat": 110.15395982997794,
    "b2_hat": 443.3312485629004,
}


def load_physics_init(path="physics_coefficients.json"):
    """Override PHYSICS_INIT from the saved coefficients file if present."""
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        return {
            "k_hat": data["tension"]["k_hat"],
            "b1_hat": data["tension"]["b1_hat"],
            "c1_hat": data["strain"]["c1_hat"],
            "c2_hat": data["strain"]["c2_hat"],
            "c3_hat": data["strain"]["c3_hat"],
            "b2_hat": data["strain"]["b2_hat"],
        }
    return PHYSICS_INIT


def resolve_column(df, candidates):
    for name in candidates:
        if name in df.columns:
            return name
    raise KeyError(f"None of {candidates} found in CSV. Actual columns: {list(df.columns)}")


def shi_to_grade(shi_raw):
    """Raw SHI tensor -> integer grade index (0 = Poor, 1 = Fair, 2 = Good)."""
    return torch.bucketize(shi_raw.contiguous(), HEALTH_EDGES.to(shi_raw.device), right=True)

# Data

class BridgeDataset(Dataset):
    """If weighted=True (use for the train split only), builds per-sample loss
    weights from health-grade rarity and heavy-load events. Otherwise weights = 1."""

    def __init__(self, csv_file, weighted=False):
        df = pd.read_csv(csv_file)

        load_col = resolve_column(df, ["Load_norm", "Vehicle_Load_tons_norm"])
        temp_col = resolve_column(df, ["Temp_norm", "Temperature_C_norm"])
        vib_col = resolve_column(df, ["Vibration_norm", "Vibration_ms2_norm"])
        elapsed_col = resolve_column(df, ["elapsed_seconds_norm"])
        hour_sin_col = resolve_column(df, ["hour_sin"])
        hour_cos_col = resolve_column(df, ["hour_cos"])
        strain_col = resolve_column(df, ["Strain_norm", "Strain_microstrain_norm"])
        tension_col = resolve_column(df, ["Tension_norm", "Cable_Member_Tension_kN_norm"])
        shi_col = resolve_column(df, ["SHI_norm", "Structural_Health_Index_SHI_norm"])

        feature_cols = [load_col, temp_col, vib_col, elapsed_col, hour_sin_col, hour_cos_col]
        self.x = torch.tensor(df[feature_cols].values, dtype=torch.float32)
        self.y_strain = torch.tensor(df[strain_col].values, dtype=torch.float32).unsqueeze(1)
        self.y_tension = torch.tensor(df[tension_col].values, dtype=torch.float32).unsqueeze(1)
        self.y_shi = torch.tensor(df[shi_col].values, dtype=torch.float32).unsqueeze(1)

        # True health grade (from denormalized SHI).
        s = STATS["Structural_Health_Index_SHI"]
        self.shi_raw = self.y_shi * s["std"] + s["mean"]
        self.grade = shi_to_grade(self.shi_raw).squeeze(1)

        self.w = torch.ones(len(self.x), 1)
        if weighted:
            n = len(self.x)
            counts = torch.bincount(self.grade, minlength=N_GRADES).float().clamp(min=1)
            grade_w = ((n / (N_GRADES * counts)) ** GRADE_WEIGHT_BETA).clamp(max=GRADE_WEIGHT_MAX)
            load_w = 1.0 + LOAD_ALPHA * self.x[:, 0].clamp(0.0, LOAD_CAP)
            w = grade_w[self.grade] * load_w
            self.w = (w / w.mean()).unsqueeze(1)  # mean weight = 1
            print("Train health-grade counts:",
                  {HEALTH_LABELS[i]: int(counts[i]) for i in range(N_GRADES)})
            print("Grade weights (before load term):",
                  {HEALTH_LABELS[i]: round(float(grade_w[i]), 2) for i in range(N_GRADES)})

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        return self.x[idx], self.y_strain[idx], self.y_tension[idx], self.y_shi[idx], self.w[idx]

# Model
class DynamicBridgePCNN(nn.Module):
    def __init__(self, stats, physics_init, dropout=DROPOUT_P, loss_mode=LOSS_MODE):
        super().__init__()
        self.stats = stats
        self.loss_mode = loss_mode

        # Shared backbone: 6 -> 64 -> 64 -> 64 (tanh + dropout)
        self.backbone = nn.Sequential(
            nn.Linear(6, 64), nn.Tanh(), nn.Dropout(dropout),
            nn.Linear(64, 64), nn.Tanh(), nn.Dropout(dropout),
            nn.Linear(64, 64), nn.Tanh(), nn.Dropout(dropout),
        )

        def head():
            return nn.Sequential(nn.Linear(64, 32), nn.Tanh(), nn.Dropout(dropout), nn.Linear(32, 1))

        self.strain_head, self.tension_head, self.shi_head = head(), head(), head()

        # Learnable physics constants, warm-started at the train-split fit.
        for name in ["k_hat", "b1_hat", "c1_hat", "c2_hat", "c3_hat", "b2_hat"]:
            setattr(self, name, nn.Parameter(torch.tensor(physics_init[name], dtype=torch.float32)))

        # (data_strain, data_tension, data_shi, phys_strain, phys_tension)
        self.log_vars = nn.Parameter(torch.zeros(5))

    def forward(self, x):
        f = self.backbone(x)
        return self.strain_head(f), self.tension_head(f), self.shi_head(f)

    def _denorm(self, key, norm_val):
        s = self.stats[key]
        return norm_val * s["std"] + s["mean"]

    def compute_loss(self, x, y_strain, y_tension, y_shi, w, return_components=False):
        p_strain, p_tension, p_shi = self.forward(x)

        def wmse(pred, target):  # sample-weighted MSE
            return (w * (pred - target) ** 2).mean()

        # 1. Data losses (normalized space, sample-weighted).
        l_d_strain = wmse(p_strain, y_strain)
        l_d_tension = wmse(p_tension, y_tension)
        l_d_shi = wmse(p_shi, y_shi)

        # 2. Physics residuals in real units, rescaled by target variance.
        load_raw = self._denorm("Vehicle_Load_tons", x[:, 0:1])
        vib_raw = self._denorm("Vibration_ms2", x[:, 2:3])
        p_strain_raw = self._denorm("Strain_microstrain", p_strain)
        p_tension_raw = self._denorm("Cable_Member_Tension_kN", p_tension)

        phys_tension = self.k_hat * load_raw + self.b1_hat
        phys_strain = (self.c1_hat * load_raw + self.c2_hat * load_raw ** 2
                       + self.c3_hat * vib_raw + self.b2_hat)

        strain_var = self.stats["Strain_microstrain"]["std"] ** 2
        tension_var = self.stats["Cable_Member_Tension_kN"]["std"] ** 2
        l_p_strain = wmse(p_strain_raw, phys_strain) / strain_var
        l_p_tension = wmse(p_tension_raw, phys_tension) / tension_var

        # 3. Combine terms.
        losses = [l_d_strain, l_d_tension, l_d_shi, l_p_strain, l_p_tension]
        if self.loss_mode == "uncertainty":
            total = 0.0
            for i, l in enumerate(losses):
                total = total + 0.5 * torch.exp(-self.log_vars[i]) * l + 0.5 * self.log_vars[i]
        else:  # fixed lambdas
            lam = list(FIXED_LAMBDAS.values())
            total = sum(lam[i] * l for i, l in enumerate(losses))

        if return_components:
            return total, {k: l.item() for k, l in zip(FIXED_LAMBDAS.keys(), losses)}
        return total

# Evaluation
@torch.no_grad()
def evaluate_rmse(model, loader):
    """Deterministic (dropout off) RMSE per head in physical units."""
    model.eval()
    sq = {"strain": 0.0, "tension": 0.0, "shi": 0.0}
    n = 0
    for x_b, ys_b, yt_b, yshi_b, _ in loader:
        x_b, ys_b, yt_b, yshi_b = (t.to(DEVICE) for t in (x_b, ys_b, yt_b, yshi_b))
        ps, pt, pshi = model(x_b)
        for name, key, p, y in [
            ("strain", "Strain_microstrain", ps, ys_b),
            ("tension", "Cable_Member_Tension_kN", pt, yt_b),
            ("shi", "Structural_Health_Index_SHI", pshi, yshi_b),
        ]:
            sq[name] += ((model._denorm(key, p) - model._denorm(key, y)) ** 2).sum().item()
        n += x_b.size(0)
    return {k: (v / n) ** 0.5 for k, v in sq.items()}


def normalized_val_score(rmse):
    """Sum of normalized data MSEs (unweighted) — used for checkpoint selection."""
    s = STATS
    return ((rmse["strain"] / s["Strain_microstrain"]["std"]) ** 2
            + (rmse["tension"] / s["Cable_Member_Tension_kN"]["std"]) ** 2
            + (rmse["shi"] / s["Structural_Health_Index_SHI"]["std"]) ** 2)


@torch.no_grad()
def mc_predict(model, dataset, n_samples=MC_SAMPLES):
    """Monte Carlo Dropout: T stochastic forward passes with dropout ON.
    Returns raw-unit samples of shape (T, N, 3) = [strain, tension, SHI]."""
    model.eval()
    for m in model.modules():
        if isinstance(m, nn.Dropout):
            m.train()  # keep dropout active; nothing else has train-only behaviour
    x = dataset.x.to(DEVICE)
    samples = []
    for _ in range(n_samples):
        ps, pt, pshi = model(x)
        samples.append(torch.cat([
            model._denorm("Strain_microstrain", ps),
            model._denorm("Cable_Member_Tension_kN", pt),
            model._denorm("Structural_Health_Index_SHI", pshi),
        ], dim=1))
    model.eval()
    return torch.stack(samples).cpu()


def grade_probabilities(shi_samples):
    """(T, N) SHI samples -> (N, K) probability of each health grade."""
    grades = shi_to_grade(shi_samples)                     # (T, N)
    return F.one_hot(grades, N_GRADES).float().mean(dim=0)  # (N, K)


def evaluate_uncertainty(model, dataset, n_samples=MC_SAMPLES, save_csv=None):
    save_csv = save_csv or out_path("test_predictions_mc.csv")
    samples = mc_predict(model, dataset, n_samples)         # (T, N, 3)
    mean, std = samples.mean(0), samples.std(0)
    lo, hi = torch.quantile(samples, 0.025, dim=0), torch.quantile(samples, 0.975, dim=0)

    s = STATS
    truth = torch.cat([
        dataset.y_strain * s["Strain_microstrain"]["std"] + s["Strain_microstrain"]["mean"],
        dataset.y_tension * s["Cable_Member_Tension_kN"]["std"] + s["Cable_Member_Tension_kN"]["mean"],
        dataset.shi_raw,
    ], dim=1)

    print(f"\nMC Dropout ({n_samples} passes) — mean prediction vs truth")
    for i, (name, unit) in enumerate([("Strain", "microstrain"), ("Tension", "kN"), ("SHI", "")]):
        rmse = ((mean[:, i] - truth[:, i]) ** 2).mean().sqrt().item()
        cover = ((truth[:, i] >= lo[:, i]) & (truth[:, i] <= hi[:, i])).float().mean().item()
        print(f"  {name:8s} RMSE {rmse:.4f} {unit} | mean pred. std {std[:, i].mean():.4f} "
              f"| 95% interval coverage {cover * 100:.1f}%")

    probs = grade_probabilities(samples[:, :, 2])           # (N, K)
    true_grade = dataset.grade
    pred_grade = probs.argmax(dim=1)
    onehot = F.one_hot(true_grade, N_GRADES).float()
    acc = (pred_grade == true_grade).float().mean().item()
    brier = ((probs - onehot) ** 2).sum(dim=1).mean().item()
    print(f"\nGraded health probabilities — accuracy {acc * 100:.2f}% | Brier score {brier:.4f}")
    counts = torch.bincount(true_grade, minlength=N_GRADES)
    print("  True grade counts:", {HEALTH_LABELS[i]: int(counts[i]) for i in range(N_GRADES)})

    out = pd.DataFrame({
        "strain_mean": mean[:, 0].numpy(), "strain_std": std[:, 0].numpy(),
        "tension_mean": mean[:, 1].numpy(), "tension_std": std[:, 1].numpy(),
        "shi_mean": mean[:, 2].numpy(), "shi_std": std[:, 2].numpy(),
        "true_grade": [HEALTH_LABELS[g] for g in true_grade.tolist()],
        "pred_grade": [HEALTH_LABELS[g] for g in pred_grade.tolist()],
    })
    for k, label in enumerate(HEALTH_LABELS):
        out[f"P_{label}"] = probs[:, k].numpy()
    out.to_csv(save_csv, index=False)
    print(f"  Per-sample predictions saved to {save_csv}")

    # Everything the test-set graphs need (numpy, raw units).
    return {
        "mean": mean.numpy(), "std": std.numpy(), "truth": truth.numpy(),
        "lo": lo.numpy(), "hi": hi.numpy(),
        "true_grade": true_grade.numpy(), "pred_grade": pred_grade.numpy(),
        "accuracy": acc, "brier": brier,
    }

# Training
PHYSICS_NAMES = ["k_hat", "b1_hat", "c1_hat", "c2_hat", "c3_hat", "b2_hat"]


def train_pcnn(train_csv, val_csv, epochs=EPOCHS, batch_size=128, lr=3e-3, grad_clip=1.0,
               dropout=DROPOUT_P, loss_mode=LOSS_MODE, weighted=True):
    """Returns (last-epoch model, per-epoch history DataFrame, best epoch, best val score)."""
    train_ds = BridgeDataset(train_csv, weighted=weighted)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(BridgeDataset(val_csv), batch_size=batch_size, shuffle=False)
    # Plain pass over the train split (dropout off, no sample weights) used only to
    # record train RMSE each epoch. It has its own random generator so it does not
    # change the random numbers used by training: results stay reproducible.
    train_eval_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=False,
                                   generator=torch.Generator().manual_seed(0))

    model = DynamicBridgePCNN(STATS, load_physics_init(), dropout=dropout, loss_mode=loss_mode).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    term_keys = list(FIXED_LAMBDAS.keys())  # data_strain, data_tension, data_shi, phys_strain, phys_tension
    history = []
    best_val, best_epoch = float("inf"), 0
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        term_sum = {k: 0.0 for k in term_keys}
        for x_b, ys_b, yt_b, yshi_b, w_b in train_loader:
            x_b, ys_b, yt_b, yshi_b, w_b = (t.to(DEVICE) for t in (x_b, ys_b, yt_b, yshi_b, w_b))
            optimizer.zero_grad()
            loss, terms = model.compute_loss(x_b, ys_b, yt_b, yshi_b, w_b, return_components=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
            n_b = x_b.size(0)
            train_loss += loss.item() * n_b
            for k in term_keys:
                term_sum[k] += terms[k] * n_b
        n_train = len(train_loader.dataset)
        train_loss /= n_train

        rmse = evaluate_rmse(model, val_loader)
        val_score = normalized_val_score(rmse)
        train_rmse = evaluate_rmse(model, train_eval_loader)
        if val_score < best_val:
            best_val, best_epoch = val_score, epoch
            torch.save(model.state_dict(), out_path("best_pcnn.pt"))

        row = {"epoch": epoch, "train_loss": train_loss}
        row.update({f"term_{k}": term_sum[k] / n_train for k in term_keys})
        row.update({"val_score": val_score,
                    "val_rmse_strain": rmse["strain"], "val_rmse_tension": rmse["tension"],
                    "val_rmse_shi": rmse["shi"],
                    "train_rmse_strain": train_rmse["strain"], "train_rmse_tension": train_rmse["tension"],
                    "train_rmse_shi": train_rmse["shi"]})
        row.update({k: getattr(model, k).item() for k in PHYSICS_NAMES})
        history.append(row)

        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {train_loss:.4f} | "
                  f"Val Score: {val_score:.4f} | Val RMSE — Strain: {rmse['strain']:.2f}, "
                  f"Tension: {rmse['tension']:.2f}, SHI: {rmse['shi']:.4f}")

    print(f"\nBest checkpoint: epoch {best_epoch} (val score {best_val:.4f}); "
          f"this is the model used for the test results below.")
    return model, pd.DataFrame(history), best_epoch, best_val

# Graphs of how training went (saved as PNG beside the script)
# (key, display name, unit used on axis labels, colour)
HEADS = [  
    ("strain", "Strain", "µε", "tab:blue"),
    ("tension", "Cable tension", "kN", "tab:orange"),
    ("shi", "SHI", "SHI units", "tab:green"),
]                                                   


def _lower(name):
    """'Strain' -> 'strain', but keep the acronym 'SHI' in capitals."""
    return name if name == "SHI" else name.lower()


def _plain_log_ticks(ax):
    """Show 0.5, 1, 2 ... instead of 5×10^-1 on a log axis."""
    fmt = FuncFormatter(lambda v, _: f"{v:g}")
    ax.yaxis.set_major_formatter(fmt)
    ax.yaxis.set_minor_formatter(fmt)
PHYSICS_LABELS = {  # constant -> (equation it belongs to, unit)
    "k_hat": ("tension slope k", "kN per ton"),
    "b1_hat": ("tension offset b1", "kN"),
    "c1_hat": ("strain load coefficient c1", "µε per ton"),
    "c2_hat": ("strain load² coefficient c2", "µε per ton²"),
    "c3_hat": ("strain vibration coefficient c3", "µε per (m/s²)"),
    "b2_hat": ("strain offset b2", "µε"),
}


def _save_fig(fig, name):
    path = out_path(name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved graph: {os.path.basename(path)}")


def _mark_best(ax, best_epoch, label=True):
    ax.axvline(best_epoch, color="tab:red", linestyle="--", linewidth=1.2,
               label=f"Best checkpoint (epoch {best_epoch})" if label else None)


def plot_training_loss(hist, best_epoch):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(hist["epoch"], hist["train_loss"], color="tab:blue", linewidth=1.8, label="Training loss")
    _mark_best(ax, best_epoch)
    if (hist["train_loss"] > 0).all():
        ax.set_yscale("log")
        _plain_log_ticks(ax)
        ax.set_ylabel("Training loss (log scale)")
    else:
        ax.set_ylabel("Training loss")
    ax.set_xlabel("Epoch")
    ax.set_title("Training loss per epoch\n(all loss terms combined, sample-weighted, dropout on)")
    ax.legend()
    _save_fig(fig, "plot_1_training_loss.png")


def plot_loss_terms(hist):
    names = {"data_strain": "Data: strain", "data_tension": "Data: tension", "data_shi": "Data: SHI",
             "phys_strain": "Physics: strain", "phys_tension": "Physics: tension"}
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for k, label in names.items():
        style = "--" if k.startswith("phys") else "-"
        ax.plot(hist["epoch"], hist[f"term_{k}"], style, linewidth=1.6, label=label)
    ax.set_yscale("log")
    _plain_log_ticks(ax)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss term value, before λ weighting (log scale)")
    ax.set_title("Individual loss terms per epoch\n(data terms: normalized MSE; physics terms: rescaled by target variance)")
    ax.legend(ncol=2)
    _save_fig(fig, "plot_2_loss_terms.png")


def plot_validation_score(hist, best_epoch, best_val):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(hist["epoch"], hist["val_score"], color="tab:purple", linewidth=1.8, label="Validation score")
    _mark_best(ax, best_epoch)
    ax.scatter([best_epoch], [best_val], color="tab:red", zorder=5, s=45,
               label=f"Lowest score = {best_val:.4f}")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Validation score\n(sum of normalized squared errors; lower = better)")
    ax.set_title("Validation score per epoch (used to choose the saved model)")
    ax.legend()
    _save_fig(fig, "plot_3_validation_score.png")


def plot_rmse_train_vs_val(hist, best_epoch, test_rmse):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
    for ax, (key, name, unit, color) in zip(axes, HEADS):
        ax.plot(hist["epoch"], hist[f"train_rmse_{key}"], color=color, linewidth=1.6,
                label="Train RMSE (dropout off)")
        ax.plot(hist["epoch"], hist[f"val_rmse_{key}"], color="black", linewidth=1.4, label="Validation RMSE")
        ax.axhline(test_rmse[key], color="gray", linestyle=":", linewidth=1.5,
                   label=f"Test RMSE of best checkpoint ({test_rmse[key]:.4g})")
        _mark_best(ax, best_epoch)
        ax.set_xlabel("Epoch")
        ax.set_ylabel(f"RMSE ({unit})")
        ax.set_title(f"{name}: train vs validation error")
        ax.legend(fontsize=8)
    fig.suptitle("A large, growing gap between train and validation would indicate overfitting", y=1.02, fontsize=10)
    fig.tight_layout(w_pad=3.0)
    _save_fig(fig, "plot_4_rmse_train_vs_val.png")


def plot_physics_constants(hist, best_epoch, physics_init):
    fig, axes = plt.subplots(2, 3, figsize=(15, 7))
    for ax, name in zip(axes.ravel(), PHYSICS_NAMES):
        title, unit = PHYSICS_LABELS[name]
        ax.plot(hist["epoch"], hist[name], color="tab:blue", linewidth=1.6, label="Learned value")
        ax.axhline(physics_init[name], color="gray", linestyle="--", linewidth=1.2,
                   label=f"Regression start ({physics_init[name]:.4g})")
        _mark_best(ax, best_epoch, label=False)
        ax.set_xlabel("Epoch")
        ax.set_ylabel(f"{name} ({unit})")
        ax.set_title(title)
        ax.legend(fontsize=8)
    fig.suptitle("Learnable physics constants during training (red dashed line = best checkpoint epoch)", y=1.0)
    fig.tight_layout()
    _save_fig(fig, "plot_5_physics_constants.png")


def plot_test_fit(mc):
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.5))
    for i, (key, name, unit, color) in enumerate(HEADS):
        truth, pred = mc["truth"][:, i], mc["mean"][:, i]
        err = pred - truth
        rmse = float(np.sqrt(np.mean(err ** 2)))
        lo_, hi_ = min(truth.min(), pred.min()), max(truth.max(), pred.max())

        ax = axes[0, i]
        ax.scatter(truth, pred, s=3, alpha=0.25, color=color, rasterized=True)
        ax.plot([lo_, hi_], [lo_, hi_], "k--", linewidth=1, label="Perfect prediction (y = x)")
        ax.set_xlabel(f"True {_lower(name)} ({unit})")
        ax.set_ylabel(f"Predicted {_lower(name)}, MC mean ({unit})")
        ax.set_title(f"{name}: predicted vs true (test set)")
        ax.legend(loc="upper left", fontsize=8)

        ax = axes[1, i]
        ax.hist(err, bins=60, color=color, alpha=0.8)
        ax.axvline(0, color="k", linestyle="--", linewidth=1)
        ax.set_xlabel(f"Prediction error, predicted − true ({unit})")
        ax.set_ylabel("Number of test samples")
        ax.set_title(f"{name}: error distribution")
        ax.text(0.97, 0.95, f"RMSE = {rmse:.4g}\nmean error = {err.mean():.3g}",
                transform=ax.transAxes, ha="right", va="top", fontsize=9,
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
    fig.tight_layout()
    _save_fig(fig, "plot_6_test_fit.png")


def plot_mc_calibration(mc):
    names = [h[1] for h in HEADS]
    colors = [h[3] for h in HEADS]
    cover, ratio = [], []
    for i in range(3):
        t, lo_, hi_ = mc["truth"][:, i], mc["lo"][:, i], mc["hi"][:, i]
        cover.append(100.0 * np.mean((t >= lo_) & (t <= hi_)))
        rmse = float(np.sqrt(np.mean((mc["mean"][:, i] - t) ** 2)))
        ratio.append(float(mc["std"][:, i].mean()) / rmse)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6))
    bars = a1.bar(names, cover, color=colors)
    a1.axhline(95, color="k", linestyle="--", linewidth=1.2, label="Target: 95%")
    a1.bar_label(bars, fmt="%.1f%%", padding=2)
    a1.set_ylim(0, 125)
    a1.set_xlabel("Model output")
    a1.set_ylabel("Share of true values inside the 95% MC interval (%)")
    a1.set_title("Interval coverage (test set)\nabove 95% = intervals too wide, below = too narrow")
    a1.legend(loc="upper center")

    bars = a2.bar(names, ratio, color=colors)
    a2.axhline(1.0, color="k", linestyle="--", linewidth=1.2, label="Ideal: 1.0")
    a2.bar_label(bars, fmt="%.2f", padding=2)
    a2.set_ylim(0, max(max(ratio), 1.0) * 1.3)
    a2.set_xlabel("Model output")
    a2.set_ylabel("Mean predictive std ÷ RMSE (no unit)")
    a2.set_title("Claimed uncertainty vs actual error\nabove 1 = under-confident, below 1 = over-confident")
    a2.legend(loc="upper center")
    fig.tight_layout()
    _save_fig(fig, "plot_7_mc_calibration.png")


def plot_grade_confusion(mc):
    true_g, pred_g = mc["true_grade"], mc["pred_grade"]
    cm = np.zeros((N_GRADES, N_GRADES), dtype=int)
    for t, p in zip(true_g, pred_g):
        cm[t, p] += 1
    row_tot = cm.sum(axis=1, keepdims=True)
    share = np.divide(cm, row_tot, out=np.zeros(cm.shape), where=row_tot > 0)

    fig, ax = plt.subplots(figsize=(6.8, 5.6))
    im = ax.imshow(share, cmap="Blues", vmin=0, vmax=1)
    for r in range(N_GRADES):
        for c in range(N_GRADES):
            ax.text(c, r, f"{cm[r, c]}\n({share[r, c] * 100:.0f}%)", ha="center", va="center",
                    color="white" if share[r, c] > 0.6 else "black", fontsize=9)
    ax.set_xticks(range(N_GRADES))
    ax.set_xticklabels(HEALTH_LABELS)
    ax.set_yticks(range(N_GRADES))
    ax.set_yticklabels(HEALTH_LABELS)
    ax.set_xlabel("Predicted health grade (most-voted over the MC passes)")
    ax.set_ylabel("True health grade (from true SHI)")
    ax.set_title(f"Health-grade confusion matrix (test set)\naccuracy {mc['accuracy'] * 100:.2f}%, "
                 f"Brier score {mc['brier']:.4f}")
    fig.colorbar(im, ax=ax, label="Share of samples with that true grade")
    _save_fig(fig, "plot_8_grade_confusion.png")


def make_all_plots(hist, best_epoch, best_val, physics_init, test_rmse, mc):
    """Draws every graph. A failure in one graph never stops the others."""
    if plt is None:
        print("\nmatplotlib is not installed, so graphs were skipped "
              "(pip install matplotlib). The per-epoch numbers are in "
              f"{RUN_NAME}_training_history.csv.")
        return
    plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.3, "font.size": 10})
    print("\nSaving training graphs:")
    jobs = [
        ("training loss", lambda: plot_training_loss(hist, best_epoch)),
        ("loss terms", lambda: plot_loss_terms(hist)),
        ("validation score", lambda: plot_validation_score(hist, best_epoch, best_val)),
        ("train vs validation RMSE", lambda: plot_rmse_train_vs_val(hist, best_epoch, test_rmse)),
        ("physics constants", lambda: plot_physics_constants(hist, best_epoch, physics_init)),
        ("test fit", lambda: plot_test_fit(mc)),
        ("MC calibration", lambda: plot_mc_calibration(mc)),
        ("grade confusion", lambda: plot_grade_confusion(mc)),
    ]
    for label, job in jobs:
        try:
            job()
        except Exception as exc:  # keep going; report which graph failed
            plt.close("all")
            print(f"  Could not draw '{label}' graph: {exc!r}")


if __name__ == "__main__":
    model, history, best_epoch, best_val = train_pcnn(TRAIN_CSV, VAL_CSV)
    history.to_csv(out_path("training_history.csv"), index=False)  # every epoch, for re-plotting

    test_ds = BridgeDataset(TEST_CSV)  # FIX: was train.csv
    test_loader = DataLoader(test_ds, batch_size=128, shuffle=False)
    model.load_state_dict(torch.load(out_path("best_pcnn.pt"), map_location=DEVICE))

    test_rmse = evaluate_rmse(model, test_loader)
    print(f"\nFinal Test RMSE (dropout off) — Strain: {test_rmse['strain']:.2f} microstrain, "
          f"Tension: {test_rmse['tension']:.2f} kN, SHI: {test_rmse['shi']:.4f}")

    mc = evaluate_uncertainty(model, test_ds)

    print(f"\nLearned physics constants — k_hat={model.k_hat.item():.4f}, "
          f"b1_hat={model.b1_hat.item():.4f}, c1_hat={model.c1_hat.item():.4f}, "
          f"c2_hat={model.c2_hat.item():.4f}, c3_hat={model.c3_hat.item():.4f}, "
          f"b2_hat={model.b2_hat.item():.4f}")

    with open(out_path("metrics.json"), "w") as f:
        json.dump({
            "run_name": RUN_NAME,
            "loss_mode": LOSS_MODE,
            "dropout": DROPOUT_P,
            "fixed_lambdas": FIXED_LAMBDAS,
            "epochs": len(history),
            "best_epoch": best_epoch,
            "best_val_score": best_val,
            "test_rmse": test_rmse,
            "physics_constants": {k: getattr(model, k).item()
                                  for k in ["k_hat", "b1_hat", "c1_hat", "c2_hat", "c3_hat", "b2_hat"]},
        }, f, indent=2)
    make_all_plots(history, best_epoch, best_val, load_physics_init(), test_rmse, mc)

    print(f"\nSaved {RUN_NAME}_metrics.json, {RUN_NAME}_run_log.txt, {RUN_NAME}_best_pcnn.pt, "
          f"{RUN_NAME}_training_history.csv and {RUN_NAME}_test_predictions_mc.csv in", OUT_DIR)
