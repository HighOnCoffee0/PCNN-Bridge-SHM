# Physics-Constrained Neural Network (PCNN) for Bridge Structural Health Monitoring

A multi-head, physics-constrained neural network that predicts **strain**, **cable tension** and the **Structural Health Index (SHI)** of a bridge from load, temperature, vibration and time. It combines data fitting with empirically validated physical relations (learnable constants), and quantifies uncertainty with **Monte Carlo Dropout**, giving 95% intervals and graded health probabilities.

---

## Table of Contents
1. [Motivation](#motivation)
2. [Highlights](#highlights)
3. [Dataset](#dataset)
4. [Feature Investigation and Physics Discovery](#feature-investigation-and-physics-discovery)
5. [Data Pipeline](#data-pipeline)
6. [Model Architecture](#model-architecture)
7. [Loss Function](#loss-function)
8. [Uncertainty and Graded Health Probabilities](#uncertainty-and-graded-health-probabilities)
9. [Training Setup](#training-setup)
10. [Results](#results)
11. [Limitations](#limitations)
12. [Repository Structure](#repository-structure)
13. [Getting Started](#getting-started)
14. [Outputs](#outputs)
15. [Future Work](#future-work)
16. [Acknowledgements](#acknowledgements)

---

## Motivation

Periodic bridge inspections can miss rapid or progressive changes between inspection intervals, and they are costly. A reliable monitoring system should not only learn from measured data but also stay consistent with the physical behaviour of the structure. This project builds a temporal PCNN that:

- incorporates physical constraints of bridge behaviour into the network,
- estimates structural condition from monitoring data, and
- evaluates whether the predictions are physically consistent and well calibrated.

## Highlights

- **Test-before-assume methodology**: every candidate physics relationship was tested (individual R², combined R², redundancy/proxy check, autocorrelation-artifact check) before being used. Several textbook assumptions were disproved by the data (see [Feature Investigation](#feature-investigation-and-physics-discovery)).
- **Algebraic physics loss**: the physics is purely algebraic (no derivatives), so no autodiff or PDE machinery is needed, unlike typical PDE-based PINNs.
- **Learnable physics constants**: six global scalars, warm-started from a train-split regression fit and refined during training.
- **Leak-free pipeline**: chronological 20/5/5-day split, with normalization and physics coefficients fit on the training split only.
- **Uncertainty quantification**: MC Dropout (T = 50) gives predictive mean, std and 95% intervals, plus health-grade probabilities (Poor / Fair / Good).
- **Weighted losses**: per-sample weights (rare health grades and heavy-load events) and per-term weights (fixed or learned homoscedastic).
- **Ablation**: fixed-weight physics loss compared against no physics and learned homoscedastic weighting.

## Dataset

A synthetic **Bridge SHM Digital Twin** dataset from Kaggle (`https://www.kaggle.com/datasets/mithil27360/digital-twin-bridge-structural-health-monitoring`).

| Property | Value |
|---|---|
| Rows | 43,200 (1-minute resolution, 30 days) |
| Columns | 48 (47 numeric + 1 categorical) |

Columns cover structural response sensors, environmental sensors, loading/traffic sensors, and derived indices (SHI, SHI forecasts, probability of failure, etc.). The EDA (`EDA_SUMMARY_REPORT.md`) found, among other things:

- Strongly redundant groups, e.g. Vehicle Load ↔ Traffic Volume (r = 0.996), SHI ↔ SHI_Predicted_24h (r = 0.998), Water Level ↔ Water Flow (r = 0.999).
- Heavy right skew and heavy tails in Strain, Vibration and several environmental channels.
- SHI is left-skewed (min 0.292, mean 0.816, max 0.908); about 7% of SHI values are IQR outliers.

> The data was generated synthetically and the source publishes no generation formulae, so every physical relationship had to be inferred empirically.

## Feature Investigation and Physics Discovery

### Final feature set

| Inputs (6 after time encoding) | Outputs (3 heads) |
|---|---|
| `Vehicle_Load_tons` | `Strain_microstrain` |
| `Temperature_C` | `Cable_Member_Tension_kN` |
| `Vibration_ms2` | `Structural_Health_Index_SHI` |
| `elapsed_seconds` (slow drift) | |
| `hour_sin`, `hour_cos` (daily cycle) | |

### Physics relationships (fit by OLS on the training split)

| Output | Relation | Coefficients | R² |
|---|---|---|---|
| Cable tension | `T ≈ k·Load + b₁` | k = 8.5807, b₁ = 322.174 | 0.961 |
| Strain | `ε ≈ c₁·Load + c₂·Load² + c₃·Vibration + b₂` | c₁ = 0.8619, c₂ = 0.5681, c₃ = 110.154, b₂ = 443.331 | 0.873 |
| SHI | No residual: near-deterministic function of Strain, Tilt, Deflection and Vibration; kept as a plain supervised head | formula used only for reporting / consistency checks | 0.997 (reconstruction) |

### Key findings

- **Tension is driven by Load, not by Strain.** The assumed constitutive law (`T = E·A·Strain`) gave R² = 0.75, while Tension vs Load gave R² = 0.96. The physics residual was therefore built on Load.
- **Strain has a genuine nonlinear component** (Load²) **and an independent dynamic driver (Vibration)**. Vibration raised R² by about 0.10, an order of magnitude more than any other candidate, and is largely independent of Load.
- **Temperature contributes nothing** to Tension or Strain in any functional form tested.
- **SHI is a composite index.** Its formula was reconstructed as `SHI ≈ 0.9987 − 0.0001·Strain − 0.0013·Tilt − 0.0066·Deflection − 0.0133·Vibration`. Crack propagation and acoustic emissions are not wired into SHI in this generator.
- **SHI was deliberately given no physics residual** to avoid duplicating the data loss and to avoid inter-head error propagation early in training.

### Rejected candidates (each with a documented reason)

| Category | Examples | Reason |
|---|---|---|
| Proxies of Load | Bearing_Joint_Forces, Traffic_Volume, Axle_Counts, Localized_Stress_Index | R² ≥ 0.95 explained by Load alone |
| Negligible gain | Humidity, Load_rate, Temp_rate, Load×Temp | Improvement below the 0.01–0.02 threshold |
| Autocorrelation artifact | Strain_lag1 | Slope ≈ 0.97, so persistence rather than causality |
| Uncoupled / inert | Corrosion, Crack_Propagation, Acoustic_Emissions, Wind, Water level | Near-zero correlation with targets |
| Circular | Modal_Frequency as input to Strain | Output used to predict another output |
| Forecast targets | SHI_Predicted_24h/7d/30d, Probability_of_Failure | Correlated by construction; future extension |

### Removed from scope

- **Modal_Frequency_Hz**: ceiling R² ≈ 0.52 (Temperature + Load) with no further driver found despite exhaustive search.
- **Stiffness**: derivable only from Modal Frequency, so removed with it.

A full write-up is in `PCNN_Findings_Report.docx`.

## Data Pipeline

1. **Chronological split, no shuffling**: 20 days train / 5 val / 5 test (28,800 / 7,200 / 7,200 rows).
2. **Z-score normalization** fit on the train split only, applied to val and test.
3. **Time encoding**: `elapsed_seconds` plus `hour_sin` / `hour_cos`.
4. **Physics coefficients** fit on the train split only and saved to `physics_coefficients.json`.
5. **Outliers kept**: confirmed as genuine heavy-load events, not sensor errors.

## Model Architecture

```
Input (6): load, temperature, vibration, elapsed_seconds, hour_sin, hour_cos
   │
Shared backbone: Linear(6→64) → tanh → Dropout
                 Linear(64→64) → tanh → Dropout
                 Linear(64→64) → tanh → Dropout
   │
   ├── Strain head:  64 → 32 → 1
   ├── Tension head: 64 → 32 → 1
   └── SHI head:     64 → 32 → 1

Learnable global physics scalars (not network outputs):
   k_hat, b1_hat, c1_hat, c2_hat, c3_hat, b2_hat
```

## Loss Function

Total loss: `L = Σᵢ λᵢ · Lᵢ` over five terms: three data losses (strain, tension, SHI) and two physics losses (strain, tension).

- **Data loss**: sample-weighted MSE in normalized space (MSE is used for training, RMSE for reporting).
- **Physics loss**: computed in real, de-normalized units so the constants stay physically interpretable, then divided by the target variance so terms are comparable in magnitude. It uses only the inputs, never the true labels:

  ```
  L_phys,T = mean( w · (T̂ − (k·Load + b₁))² ) / σ_T²
  L_phys,ε = mean( w · (ε̂ − (c₁·Load + c₂·Load² + c₃·Vib + b₂))² ) / σ_ε²
  ```

- **Term weighting** (`LOSS_MODE`):
  - `fixed`: manual lambdas (data = 1.0, physics = 0.1). This is the final setting.
  - `uncertainty`: learned homoscedastic weights (Kendall et al.), `½·exp(−log σᵢ²)·Lᵢ + ½·log σᵢ²`.
- **Per-sample weights** (train split only): inverse-frequency health-grade weighting (exponent 0.5, cap 5.0) multiplied by a heavy-load factor `1 + 0.5·clamp(load_z, 0, 3)`, normalized to mean 1.
- **Gradient clipping** at max-norm 1.0.
- **Checkpoint selection** on the *unweighted* validation error in normalized units (sum of the three data MSEs).

## Uncertainty and Graded Health Probabilities

- **MC Dropout**: dropout (p = 0.1) stays active at inference; T = 50 stochastic passes give a predictive mean, std and 95% interval for each head.
- **Health grades** from SHI: **Poor** (< 0.75), **Fair** (0.75 to < 0.85), **Good** (≥ 0.85). The earlier "Critical" grade was merged into Poor because the test split has no Critical samples.
- Each MC pass votes for a grade; the vote share gives `P(Poor)`, `P(Fair)`, `P(Good)` per sample, and the most-voted grade is the prediction.
- **Metrics**: RMSE (physical units), 95% interval coverage, uncertainty ratio (mean predictive std ÷ RMSE, ideal 1), grade accuracy and Brier score.

## Training Setup

| Setting | Value |
|---|---|
| Optimizer | Adam, lr = 3×10⁻³ |
| Batch size | 128 |
| Epochs | 70 |
| Gradient clipping | max-norm 1.0 |
| Activation | tanh |
| Dropout | 0.1 after every hidden layer |
| Loss weights | data 1.0, physics 0.1 |
| Sample weights | grade exponent 0.5 (cap 5.0), load factor 0.5 (cap 3.0) |
| MC Dropout | 50 passes, 95% interval |
| Random seed | 3408 |

## Results

All results are on the held-out **test split** (final 5 days), using the checkpoint with the best validation score.

### Point-prediction error (MC mean)

| Output | RMSE |
|---|---|
| Strain | 47.54 µε |
| Cable tension | 16.61 kN |
| SHI | 0.0072 |

### Health-grade classification (test)

| True \ Predicted | Poor | Fair | Good |
|---|---|---|---|
| **Poor** (882) | 882 | 0 | 0 |
| **Fair** (4,795) | 14 | 4,561 | 220 |
| **Good** (1,523) | 0 | 37 | 1,486 |

Accuracy ≈ 96.2%, Brier score = 0.0556.

### Ablation: loss weighting

| Metric | Fixed (with physics) | No physics | Homoscedastic |
|---|---|---|---|
| Grade accuracy (%) | **96.50** | 95.00 | 94.83 |
| Brier score (↓) | **0.0556** | 0.0693 | 0.0748 |
| Validation score (↓) | 0.1194 | **0.1089** | 0.1601 |
| 95% coverage, strain | **92.9** | 85.8 | 77.7 |
| 95% coverage, tension | **69.3** | 66.1 | 60.6 |
| 95% coverage, SHI | **93.8** | 83.0 | 84.4 |
| Std ÷ error, strain (ideal 1) | 1.14 | **0.96** | 0.71 |
| Std ÷ error, tension | **0.58** | 0.54 | 0.48 |
| Std ÷ error, SHI | 1.15 | **0.85** | 0.94 |

### Observations

- Fixed physics weights give the best grade accuracy, Brier score and interval coverage on all three outputs. The Brier score is about 20% lower than with no physics and about 26% lower than with homoscedastic weighting.
- The physics term improved calibration the most: SHI coverage rose from 83.0% to 93.8% and strain coverage from 85.8% to 92.9%. SHI has no physics term of its own, so the benefit probably comes through the shared backbone acting as a regularizer.
- Learned homoscedastic weighting performed *worse than no physics*. The physics terms were probably driven toward very large weights, over-trusting formulas that explain only 87–96% of the variance.
- A physics weight of 0.1 lets the physics regularize the model without overriding the data.
- Selecting on validation score alone would favour "no physics". The physics-constrained model wins on calibration and grade metrics.

## Limitations

- **Synthetic data**: the generator's formulae are unknown, so the discovered "physics" describes this dataset, not a real bridge.
- **No extreme-load events in the test split**: the model has not been tested on the heaviest loading regime.
- **Tension intervals are over-confident**: 95% coverage is only 69.3% and the uncertainty ratio is 0.58. Predictions also cluster by load regime (see the predicted-vs-true plot).
- **Short horizon**: only 30 days, so slow degradation processes (corrosion, fatigue, crack growth) cannot be learned.
- **Physics is approximate**: the strain and tension relations explain 87–96% of the variance, not 100%.
- **SHI grade boundaries** are manually chosen and adjustable (`HEALTH_EDGES`).

## Repository Structure

```
.
├── Output/
│   ├── *_best_pcnn.pt	Best checkpoint (by validation score)
│   ├── *_metrics.json	                    #Config, best epoch, test RMSE, learned physics constants
│   ├── *_training_history.csv	           #Per-epoch losses, RMSEs and physics constants
│   ├── *_test_predictions_mc.csv	        #Per-sample MC mean/std, grade probabilities, predicted grade
│   ├── *_run_log.txt	                    #Full console log
│   ├── *_plot_1_training_loss.png	        #Total training loss
│   ├── *_plot_2_loss_terms.png	           #Individual loss terms (log scale)
│   ├── *_plot_3_validation_score.png	     #Checkpoint-selection score
│   ├── *_plot_4_rmse_train_vs_val.png	     #Train vs validation RMSE per output
│   ├── *_plot_5_physics_constants.png	     #Learnable constants over training
│   ├── *_plot_6_test_fit.png	              #Predicted vs true and error histograms
│   ├── *_plot_7_mc_calibration.png	        #Interval coverage and uncertainty ratio
│   └── *_plot_8_grade_confusion.png	     #Health-grade confusion matrix
├── data/                                   # (not tracked) raw and split CSVs
│   └── Dataset.txt                         # link to kaggle dataset
├── docs/
│   ├── EDA_SUMMARY_REPORT.md               # exploratory data analysis
│   ├── PCNN_Findings_Report.docx           # full feature-investigation report
│   └── PCNN_Project_Summary.docx           # project summary
├── README.md
├── eda_reports.py                          # EDA script
├── find_coefficients.py                    # fits physics coefficients on train.csv -> physics_coefficients.json
├── physics_coefficients.json               # generated by find_coefficients.py
├── prepare_eda_subset.py                   # cleans a column subset for EDA
├── prepare_pcnn_data.py                    # chronological split + normalization + time encoding
├── train_pcnn.py                           # PCNN model, training, MC Dropout evaluation, plots


```
- Where * is your run name

## Getting Started

### Requirements

- Python 3.9+
- `torch`, `numpy`, `pandas`, `matplotlib` (matplotlib is optional; training runs without plots)

```bash
pip install torch numpy pandas matplotlib
```

### Run

1. Download the dataset from Kaggle and place it in `data/`.
2. Preprocess and split:
   ```bash
   python prepare_pcnn_data.py
   python find_coefficients.py
   python validate_preprocessed_data.py
   ```
3. Set `DATA_DIR` at the top of `train_pcnn.py` to the folder containing `train.csv`, `val.csv` and `test.csv`.
4. Train and evaluate:
   ```bash
   python train_pcnn.py
   ```

### Key configuration (top of `train_pcnn.py`)

| Variable | Meaning |
|---|---|
| `RUN_NAME` | Prefix for all output files; change per experiment |
| `LOSS_MODE` | `"fixed"` or `"uncertainty"` (homoscedastic) |
| `FIXED_LAMBDAS` | Per-term weights |
| `DROPOUT_P`, `MC_SAMPLES` | MC Dropout settings |
| `HEALTH_LABELS`, `HEALTH_EDGES` | Health-grade names and SHI cut-offs |
| `GRADE_WEIGHT_*`, `LOAD_*` | Per-sample weighting parameters |
| `EPOCHS` | Number of training epochs |

To reproduce the **no-physics** ablation, set the physics lambdas to 0. To reproduce the **homoscedastic** run, set `LOSS_MODE = "uncertainty"`.

## Outputs

All outputs are saved next to the script, prefixed with `RUN_NAME`:

| File | Content |
|---|---|
| `*_best_pcnn.pt` | Best checkpoint (by validation score) |
| `*_metrics.json` | Config, best epoch, test RMSE, learned physics constants |
| `*_training_history.csv` | Per-epoch losses, RMSEs and physics constants |
| `*_test_predictions_mc.csv` | Per-sample MC mean/std, grade probabilities, predicted grade |
| `*_run_log.txt` | Full console log |
| `*_plot_1_training_loss.png` | Total training loss |
| `*_plot_2_loss_terms.png` | Individual loss terms (log scale) |
| `*_plot_3_validation_score.png` | Checkpoint-selection score |
| `*_plot_4_rmse_train_vs_val.png` | Train vs validation RMSE per output |
| `*_plot_5_physics_constants.png` | Learnable constants over training |
| `*_plot_6_test_fit.png` | Predicted vs true and error histograms |
| `*_plot_7_mc_calibration.png` | Interval coverage and uncertainty ratio |
| `*_plot_8_grade_confusion.png` | Health-grade confusion matrix |

- Where * is your run name

## Future Work

- Add Modal Frequency back with a stronger physical grounding, and derive Stiffness.
- Forecasting heads (SHI at 24 h / 7 d / 30 d ahead, probability of failure).
- Evaluate on a split that contains extreme-load events, or on real bridge data.
- Calibrate the MC Dropout intervals (especially for tension).
- Add an SHI consistency check against the reconstructed formula as a post-training report.
- Look into explainable AI techniques

## Acknowledgements

- Synthetic Bridge SHM Digital Twin dataset from Kaggle.
- Homoscedastic multi-task weighting follows Kendall et al., *Multi-Task Learning Using Uncertainty to Weigh Losses*.
- Monte Carlo Dropout follows Gal and Ghahramani, *Dropout as a Bayesian Approximation*.
