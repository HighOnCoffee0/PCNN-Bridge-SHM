"""
 COMPREHENSIVE EXPLORATORY DATA ANALYSIS (EDA) SCRIPT
 
Generates, for ANY input CSV (all rows & columns, auto-detected):

  1. Dataset overview (shape, dtypes, memory, duplicates, missing values)
  2. Descriptive statistics (numeric + categorical)
  3. Correlation heatmap (numeric columns)
  4. Distribution histograms (+ KDE) for every numeric column
  5. Boxplots for every numeric column with IQR-based outlier detection
     -> exact outlier counts, bounds, and row-level outlier details
  6. Skewness & Kurtosis for every numeric column (table + interpretation)
  7. t-SNE 2D projection of the numeric feature space (colored by a
     categorical column if one exists)
  8. Time-series analysis (auto-detects datetime columns):
        - trend over time per numeric column
        - rolling mean/std
        - day-of-week / month seasonality
        - skewness & kurtosis of each numeric column BY time period
  9. Categorical column analysis (cardinality, top categories, bar charts)
 10. A consolidated text/markdown SUMMARY REPORT tying everything together

================================================================================
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless backend, safe for scripts/servers
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.manifold import TSNE

sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 110
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.titleweight"] = "bold"

# CONFIG

# Max unique values for a numeric-looking or object column to be treated
# as categorical for coloring / grouping purposes.
MAX_CATEGORY_CARDINALITY = 3

# For t-SNE: if the dataset has more rows than this, we still use ALL rows
# (per requirement) but we warn the user since t-SNE is O(n^2)-ish and can
# be slow on very large datasets.
TSNE_SLOW_WARNING_THRESHOLD = 20000

# Leave INPUT_CSV_PATH as None to keep using the command-line argument instead.
INPUT_CSV_PATH = r" "  # <-- change this to your CSV path
OUTPUT_DIR = r" "               # <-- change this to your desired output folder


# UTILITIES
def make_dirs(output_dir):
    plots_dir = os.path.join(output_dir, "plots")
    tables_dir = os.path.join(output_dir, "tables")
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(tables_dir, exist_ok=True)
    return plots_dir, tables_dir


def safe_filename(name):
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in str(name))


def load_data(csv_path):
    """Load the full CSV (all rows, all columns) and try to auto-detect
    datetime columns from object columns."""
    df = pd.read_csv(csv_path)

    # Try to auto-convert text-like columns that look like dates.
    # Handles both legacy 'object' dtype and pandas >=3.0's default 'str' dtype.
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            sample = df[col].dropna().astype(str).head(20)
            if len(sample) == 0:
                continue
            try:
                pd.to_datetime(sample, errors="raise", format=None, dayfirst=True)
                # If it parsed cleanly for the sample, convert the full column
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
            except Exception:
                continue
    return df


def detect_column_types(df):
    """Split columns into numeric, datetime, categorical (low cardinality),
    and high-cardinality text columns."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns.tolist()

    remaining = [c for c in df.columns if c not in numeric_cols + datetime_cols]
    categorical_cols, text_cols = [], []
    for c in remaining:
        nun = df[c].nunique(dropna=True)
        if nun <= MAX_CATEGORY_CARDINALITY:
            categorical_cols.append(c)
        else:
            text_cols.append(c)

    return numeric_cols, datetime_cols, categorical_cols, text_cols


# DATASET OVERVIEW
def dataset_overview(df, tables_dir):
    n_rows, n_cols = df.shape
    mem_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
    dup_count = df.duplicated().sum()

    missing = df.isnull().sum()
    missing_pct = (missing / n_rows * 100).round(2)
    missing_table = pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[c].dtype) for c in df.columns],
        "missing_count": missing.values,
        "missing_pct": missing_pct.values,
        "n_unique": [df[c].nunique(dropna=True) for c in df.columns],
    }).sort_values("missing_pct", ascending=False)
    missing_table.to_csv(os.path.join(tables_dir, "column_overview.csv"), index=False)

    overview = {
        "n_rows": n_rows,
        "n_cols": n_cols,
        "memory_mb": round(mem_mb, 3),
        "duplicate_rows": int(dup_count),
        "total_missing_cells": int(missing.sum()),
        "total_missing_pct": round(missing.sum() / (n_rows * n_cols) * 100, 3),
    }
    return overview, missing_table


# DESCRIPTIVE STATISTICS
def descriptive_stats(df, numeric_cols, categorical_cols, tables_dir):
    if numeric_cols:
        num_desc = df[numeric_cols].describe().T
        num_desc["range"] = num_desc["max"] - num_desc["min"]
        num_desc.to_csv(os.path.join(tables_dir, "numeric_describe.csv"))
    else:
        num_desc = pd.DataFrame()

    cat_summaries = []
    for c in categorical_cols:
        vc = df[c].value_counts(dropna=False)
        top = vc.index[0] if len(vc) else None
        cat_summaries.append({
            "column": c,
            "n_unique": df[c].nunique(dropna=True),
            "top_category": top,
            "top_freq": int(vc.iloc[0]) if len(vc) else 0,
            "top_pct": round(vc.iloc[0] / len(df) * 100, 2) if len(vc) else 0,
        })
    cat_desc = pd.DataFrame(cat_summaries)
    if not cat_desc.empty:
        cat_desc.to_csv(os.path.join(tables_dir, "categorical_describe.csv"), index=False)

    return num_desc, cat_desc

# CORRELATION HEATMAP
def plot_correlation_heatmap(df, numeric_cols, plots_dir, tables_dir):
    if len(numeric_cols) < 2:
        return None
    corr = df[numeric_cols].corr(numeric_only=True)
    corr.to_csv(os.path.join(tables_dir, "correlation_matrix.csv"))

    fig_w = max(8, 0.6 * len(numeric_cols) + 3)
    fig_h = max(6, 0.55 * len(numeric_cols) + 3)
    plt.figure(figsize=(fig_w, fig_h))
    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(
        corr, mask=mask, annot=len(numeric_cols) <= 25, fmt=".2f",
        cmap="coolwarm", center=0, square=True,
        linewidths=0.5, cbar_kws={"shrink": 0.8}
    )
    plt.title("Correlation Heatmap (Numeric Columns)")
    plt.tight_layout()
    path = os.path.join(plots_dir, "correlation_heatmap.png")
    plt.savefig(path)
    plt.close()

    # Strongest correlated pairs (excluding self-correlation)
    corr_pairs = (
        corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        .stack()
        .reset_index()
    )
    corr_pairs.columns = ["col_1", "col_2", "correlation"]
    corr_pairs["abs_corr"] = corr_pairs["correlation"].abs()
    corr_pairs = corr_pairs.sort_values("abs_corr", ascending=False).drop(columns="abs_corr")
    corr_pairs.to_csv(os.path.join(tables_dir, "top_correlated_pairs.csv"), index=False)

    return path, corr_pairs

# SKEWNESS & KURTOSIS
def interpret_skew(s):
    if pd.isna(s):
        return "N/A"
    if abs(s) < 0.5:
        return "approximately symmetric"
    elif abs(s) < 1:
        return "moderately skewed " + ("right" if s > 0 else "left")
    else:
        return "highly skewed " + ("right" if s > 0 else "left")


def interpret_kurtosis(k):
    """Uses excess kurtosis (Fisher's definition, normal = 0)."""
    if pd.isna(k):
        return "N/A"
    if abs(k) < 0.5:
        return "mesokurtic (normal-like tails)"
    elif k > 0:
        return "leptokurtic (heavier tails / more outlier-prone)"
    else:
        return "platykurtic (lighter tails / flatter peak)"


def compute_skew_kurtosis(df, numeric_cols, tables_dir):
    rows = []
    for c in numeric_cols:
        series = df[c].dropna()
        if len(series) < 3:
            continue
        sk = stats.skew(series)
        ku = stats.kurtosis(series)  # excess kurtosis (Fisher)
        rows.append({
            "column": c,
            "skewness": round(sk, 4),
            "skew_interpretation": interpret_skew(sk),
            "excess_kurtosis": round(ku, 4),
            "kurtosis_interpretation": interpret_kurtosis(ku),
        })
    result = pd.DataFrame(rows)
    if not result.empty:
        result.to_csv(os.path.join(tables_dir, "skewness_kurtosis.csv"), index=False)
    return result

# DISTRIBUTION HISTOGRAMS
def plot_distributions(df, numeric_cols, plots_dir):
    if not numeric_cols:
        return None
    n = len(numeric_cols)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 4.2 * nrows))
    axes = np.array(axes).reshape(-1)

    for i, col in enumerate(numeric_cols):
        ax = axes[i]
        data = df[col].dropna()
        sns.histplot(data, kde=True, ax=ax, color="#4C72B0", edgecolor="white")
        mean_v, median_v = data.mean(), data.median()
        ax.axvline(mean_v, color="red", linestyle="--", linewidth=1, label=f"mean={mean_v:.2f}")
        ax.axvline(median_v, color="green", linestyle="-.", linewidth=1, label=f"median={median_v:.2f}")
        ax.set_title(col)
        ax.legend(fontsize=8)

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.suptitle("Distribution Histograms (with KDE)", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = os.path.join(plots_dir, "distribution_histograms.png")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path

# BOXPLOTS + IQR-BASED OUTLIER DETECTION
def iqr_outlier_bounds(series):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return q1, q3, iqr, lower, upper


def plot_boxplots_and_outliers(df, numeric_cols, plots_dir, tables_dir):
    if not numeric_cols:
        return None, pd.DataFrame(), pd.DataFrame()

    n = len(numeric_cols)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.5 * ncols, 4.2 * nrows))
    axes = np.array(axes).reshape(-1)

    summary_rows = []
    all_outlier_records = []

    for i, col in enumerate(numeric_cols):
        ax = axes[i]
        series = df[col].dropna()
        q1, q3, iqr, lower, upper = iqr_outlier_bounds(series)

        outlier_mask = (df[col] < lower) | (df[col] > upper)
        outliers = df.loc[outlier_mask.fillna(False), col]

        sns.boxplot(y=series, ax=ax, color="#DD8452", width=0.4, fliersize=3)
        ax.set_title(f"{col}\n(outliers: {len(outliers)}, {len(outliers)/len(series)*100:.1f}%)")

        summary_rows.append({
            "column": col,
            "Q1": round(q1, 4), "Q3": round(q3, 4), "IQR": round(iqr, 4),
            "lower_bound": round(lower, 4), "upper_bound": round(upper, 4),
            "n_outliers": int(len(outliers)),
            "pct_outliers": round(len(outliers) / len(series) * 100, 2),
            "min_outlier_value": round(outliers.min(), 4) if len(outliers) else None,
            "max_outlier_value": round(outliers.max(), 4) if len(outliers) else None,
        })

        for idx, val in outliers.items():
            all_outlier_records.append({"row_index": idx, "column": col, "value": val,
                                         "lower_bound": round(lower, 4), "upper_bound": round(upper, 4)})

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.suptitle("Boxplots with IQR Outlier Bounds", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = os.path.join(plots_dir, "boxplots_outliers.png")
    plt.savefig(path, bbox_inches="tight")
    plt.close()

    outlier_summary = pd.DataFrame(summary_rows)
    outlier_detail = pd.DataFrame(all_outlier_records)
    outlier_summary.to_csv(os.path.join(tables_dir, "iqr_outlier_summary.csv"), index=False)
    if not outlier_detail.empty:
        outlier_detail.to_csv(os.path.join(tables_dir, "iqr_outlier_row_details.csv"), index=False)

    return path, outlier_summary, outlier_detail


# t-SNE 2D PROJECTION (May take longer to generate skip this if no needed or takes too long)
def plot_tsne(df, numeric_cols, categorical_cols, plots_dir):
    if len(numeric_cols) < 2:
        return None, "Skipped: fewer than 2 numeric columns available."

    n_rows = len(df)
    note = ""
    if n_rows > TSNE_SLOW_WARNING_THRESHOLD:
        note = (f"Note: t-SNE was run on all {n_rows} rows as requested; "
                f"this can be slow for datasets this large.")

    X = df[numeric_cols].copy()
    # Impute missing values (median) since t-SNE cannot handle NaNs
    X = pd.DataFrame(SimpleImputer(strategy="median").fit_transform(X), columns=numeric_cols)
    X_scaled = StandardScaler().fit_transform(X)

    perplexity = max(5, min(30, n_rows // 100 if n_rows // 100 >= 5 else 5))
    perplexity = min(perplexity, n_rows - 1)  # perplexity must be < n_samples

    tsne = TSNE(
        n_components=2, random_state=42, init="pca",
        perplexity=perplexity, learning_rate="auto"
    )
    embedding = tsne.fit_transform(X_scaled)

    plt.figure(figsize=(9, 7))
    hue_col = categorical_cols[0] if categorical_cols else None
    if hue_col:
        sns.scatterplot(
            x=embedding[:, 0], y=embedding[:, 1],
            hue=df[hue_col].astype(str).values,
            palette="tab10", s=40, alpha=0.8, edgecolor="white", linewidth=0.3
        )
        plt.legend(title=hue_col, bbox_to_anchor=(1.02, 1), loc="upper left")
    else:
        sns.scatterplot(x=embedding[:, 0], y=embedding[:, 1], s=40, alpha=0.8,
                         color="#4C72B0", edgecolor="white", linewidth=0.3)

    plt.title(f"t-SNE Projection of Numeric Features (perplexity={perplexity})")
    plt.xlabel("t-SNE dimension 1")
    plt.ylabel("t-SNE dimension 2")
    plt.tight_layout()
    path = os.path.join(plots_dir, "tsne_projection.png")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path, note

# TIME-SERIES ANALYSIS (auto-detected datetime columns)
def time_series_analysis(df, numeric_cols, datetime_cols, plots_dir, tables_dir):
    if not datetime_cols or not numeric_cols:
        return [], pd.DataFrame()

    outputs = []
    all_period_stats = []

    for dcol in datetime_cols:
        ts_df = df[[dcol] + numeric_cols].dropna(subset=[dcol]).sort_values(dcol)
        if ts_df.empty:
            continue

        # Trend + rolling mean plot
        n = len(numeric_cols)
        ncols = 2
        nrows = int(np.ceil(n / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(8 * ncols, 3.8 * nrows))
        axes = np.array(axes).reshape(-1)

        window = max(3, len(ts_df) // 30)
        for i, col in enumerate(numeric_cols):
            ax = axes[i]
            ax.plot(ts_df[dcol], ts_df[col], alpha=0.4, linewidth=0.8, label=col)
            roll = ts_df[col].rolling(window=window, min_periods=1).mean()
            ax.plot(ts_df[dcol], roll, color="red", linewidth=1.6, label=f"rolling mean ({window})")
            ax.set_title(f"{col} over {dcol}")
            ax.legend(fontsize=8)
            ax.tick_params(axis="x", rotation=30)

        for j in range(i + 1, len(axes)):
            fig.delaxes(axes[j])

        plt.suptitle(f"Trend Over Time — grouped by '{dcol}'", fontsize=15, fontweight="bold", y=1.02)
        plt.tight_layout()
        trend_path = os.path.join(plots_dir, f"time_trend_{safe_filename(dcol)}.png")
        plt.savefig(trend_path, bbox_inches="tight")
        plt.close()
        outputs.append(trend_path)

        # Seasonality: month & day-of-week boxplots
        ts_df = ts_df.copy()
        ts_df["_month"] = ts_df[dcol].dt.month_name().str[:3]
        ts_df["_dow"] = ts_df[dcol].dt.day_name().str[:3]
        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        dow_order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

        fig, axes = plt.subplots(n, 2, figsize=(12, 3.3 * n))
        axes = np.array(axes).reshape(n, 2)
        for i, col in enumerate(numeric_cols):
            sns.boxplot(data=ts_df, x="_month", y=col, order=month_order, ax=axes[i, 0], palette="viridis")
            axes[i, 0].set_title(f"{col} by Month")
            axes[i, 0].tick_params(axis="x", rotation=45)
            sns.boxplot(data=ts_df, x="_dow", y=col, order=dow_order, ax=axes[i, 1], palette="magma")
            axes[i, 1].set_title(f"{col} by Day of Week")
        plt.suptitle(f"Seasonality — grouped by '{dcol}'", fontsize=15, fontweight="bold", y=1.01)
        plt.tight_layout()
        season_path = os.path.join(plots_dir, f"seasonality_{safe_filename(dcol)}.png")
        plt.savefig(season_path, bbox_inches="tight")
        plt.close()
        outputs.append(season_path)

        # Skewness / kurtosis BY time period (year-month) for each numeric col
        ts_df["_period"] = ts_df[dcol].dt.to_period("M").astype(str)
        for col in numeric_cols:
            grouped = ts_df.groupby("_period")[col]
            for period, vals in grouped:
                vals = vals.dropna()
                if len(vals) < 3:
                    continue
                all_period_stats.append({
                    "datetime_column": dcol,
                    "period": period,
                    "numeric_column": col,
                    "n": len(vals),
                    "mean": round(vals.mean(), 4),
                    "std": round(vals.std(), 4),
                    "skewness": round(stats.skew(vals), 4),
                    "excess_kurtosis": round(stats.kurtosis(vals), 4),
                })

        # Basic time-index diagnostics
        date_range_days = (ts_df[dcol].max() - ts_df[dcol].min()).days
        inferred_freq = pd.infer_freq(ts_df[dcol].drop_duplicates().sort_values())
        gap_info = {
            "datetime_column": dcol,
            "start": str(ts_df[dcol].min()),
            "end": str(ts_df[dcol].max()),
            "span_days": date_range_days,
            "n_timestamps": ts_df[dcol].nunique(),
            "inferred_frequency": inferred_freq if inferred_freq else "irregular/could not infer",
        }
        pd.DataFrame([gap_info]).to_csv(
            os.path.join(tables_dir, f"time_index_info_{safe_filename(dcol)}.csv"), index=False
        )

    period_stats_df = pd.DataFrame(all_period_stats)
    if not period_stats_df.empty:
        period_stats_df.to_csv(os.path.join(tables_dir, "skew_kurtosis_by_time_period.csv"), index=False)

    return outputs, period_stats_df

# CATEGORICAL COLUMN ANALYSIS
def plot_categorical(df, categorical_cols, plots_dir):
    if not categorical_cols:
        return None
    n = len(categorical_cols)
    ncols = 2
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(7 * ncols, 4 * nrows))
    axes = np.array(axes).reshape(-1)

    for i, col in enumerate(categorical_cols):
        ax = axes[i]
        vc = df[col].value_counts(dropna=False).head(15)
        sns.barplot(x=vc.values, y=vc.index.astype(str), ax=ax, palette="crest")
        ax.set_title(f"{col} (top {len(vc)} categories)")
        ax.set_xlabel("count")

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.suptitle("Categorical Column Frequencies", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    path = os.path.join(plots_dir, "categorical_frequencies.png")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path

# SUMMARY REPORT
def generate_report(output_dir, csv_path, overview, missing_table, num_desc, cat_desc,
                     corr_pairs, skew_kurt, outlier_summary, tsne_note,
                     datetime_cols, period_stats_df):
    lines = []
    lines.append(f"# EDA Summary Report")
    lines.append(f"**Source file:** `{csv_path}`\n")

    lines.append("## 1. Dataset Overview")
    lines.append(f"- Rows: **{overview['n_rows']}**  |  Columns: **{overview['n_cols']}**")
    lines.append(f"- Memory usage: **{overview['memory_mb']} MB**")
    lines.append(f"- Duplicate rows: **{overview['duplicate_rows']}**")
    lines.append(f"- Total missing cells: **{overview['total_missing_cells']}** "
                  f"({overview['total_missing_pct']}% of all cells)\n")

    top_missing = missing_table[missing_table["missing_count"] > 0].head(10)
    if not top_missing.empty:
        lines.append("**Columns with the most missing values:**\n")
        lines.append(top_missing[["column", "dtype", "missing_count", "missing_pct"]].to_markdown(index=False))
        lines.append("")
    else:
        lines.append("No missing values detected in any column.\n")

    if not num_desc.empty:
        lines.append("\n## 2. Numeric Column Summary")
        lines.append(num_desc.round(3).to_markdown())
        lines.append("")

    if not cat_desc.empty:
        lines.append("\n## 3. Categorical Column Summary")
        lines.append(cat_desc.to_markdown(index=False))
        lines.append("")

    if corr_pairs is not None and not corr_pairs.empty:
        lines.append("\n## 4. Strongest Correlations (Top 10 by |r|)")
        top_corr = corr_pairs.reindex(corr_pairs["correlation"].abs().sort_values(ascending=False).index).head(10)
        lines.append(top_corr.round(3).to_markdown(index=False))
        lines.append("")

    if not skew_kurt.empty:
        lines.append("\n## 5. Skewness & Kurtosis (per numeric column)")
        lines.append(skew_kurt.to_markdown(index=False))
        lines.append("")

    if not outlier_summary.empty:
        lines.append("\n## 6. IQR-Based Outlier Summary")
        lines.append(outlier_summary.to_markdown(index=False))
        total_outliers = outlier_summary["n_outliers"].sum()
        lines.append(f"\n**Total outlier data points (IQR method) across all numeric columns: {total_outliers}**")
        lines.append("Full row-level outlier details saved to `tables/iqr_outlier_row_details.csv`\n")

    lines.append("\n## 7. t-SNE Projection")
    lines.append("2D projection of all numeric columns (standardized, missing values median-imputed). "
                  "See `plots/tsne_projection.png`.")
    if tsne_note:
        lines.append(f"\n{tsne_note}")
    lines.append("")

    if datetime_cols:
        lines.append("\n## 8. Time-Based Analysis")
        lines.append(f"Detected datetime column(s): {', '.join(datetime_cols)}")
        lines.append("Trend, rolling mean, and seasonality (month / day-of-week) plots generated "
                      "for each numeric column against each datetime column — see `plots/time_trend_*.png` "
                      "and `plots/seasonality_*.png`.")
        if not period_stats_df.empty:
            lines.append("\nMonth-by-month skewness & kurtosis is saved to "
                          "`tables/skew_kurtosis_by_time_period.csv`. Sample (first 10 rows):\n")
            lines.append(period_stats_df.head(10).to_markdown(index=False))
    else:
        lines.append("\n## 8. Time-Based Analysis")
        lines.append("No datetime column was detected in this dataset, so time-based trend/seasonality "
                      "analysis was skipped.")

    lines.append("\n## 9. All Generated Files")
    lines.append("- `plots/correlation_heatmap.png`")
    lines.append("- `plots/distribution_histograms.png`")
    lines.append("- `plots/boxplots_outliers.png`")
    lines.append("- `plots/tsne_projection.png`")
    lines.append("- `plots/categorical_frequencies.png` (if categorical columns exist)")
    lines.append("- `plots/time_trend_<col>.png`, `plots/seasonality_<col>.png` (if datetime columns exist)")
    lines.append("- `tables/*.csv` — all numeric tables backing every plot above")

    report_path = os.path.join(output_dir, "EDA_SUMMARY_REPORT.md")
    with open(report_path, "w") as f:
        f.write("\n".join(lines))
    return report_path

# MAIN
def run_eda(csv_path, output_dir="eda_output"):
    print(f"Loading data from: {csv_path}")
    df = load_data(csv_path)
    plots_dir, tables_dir = make_dirs(output_dir)

    numeric_cols, datetime_cols, categorical_cols, text_cols = detect_column_types(df)
    print(f"Detected -> numeric: {len(numeric_cols)}, datetime: {len(datetime_cols)}, "
          f"categorical: {len(categorical_cols)}, high-cardinality text: {len(text_cols)}")

    print("Computing dataset overview...")
    overview, missing_table = dataset_overview(df, tables_dir)

    print("Computing descriptive statistics...")
    num_desc, cat_desc = descriptive_stats(df, numeric_cols, categorical_cols, tables_dir)

    print("Plotting correlation heatmap...")
    corr_result = plot_correlation_heatmap(df, numeric_cols, plots_dir, tables_dir)
    corr_pairs = corr_result[1] if corr_result else pd.DataFrame()

    print("Computing skewness & kurtosis...")
    skew_kurt = compute_skew_kurtosis(df, numeric_cols, tables_dir)

    print("Plotting distribution histograms...")
    plot_distributions(df, numeric_cols, plots_dir)

    print("Plotting boxplots and detecting IQR outliers...")
    _, outlier_summary, outlier_detail = plot_boxplots_and_outliers(df, numeric_cols, plots_dir, tables_dir)

    print("Running t-SNE (this may take a moment)...")
    tsne_result = plot_tsne(df, numeric_cols, categorical_cols, plots_dir)
    tsne_note = tsne_result[1] if tsne_result else "Skipped."

    print("Running time-series analysis (if datetime columns found)...")
    _, period_stats_df = time_series_analysis(df, numeric_cols, datetime_cols, plots_dir, tables_dir)

    print("Plotting categorical frequencies...")
    plot_categorical(df, categorical_cols, plots_dir)

    print("Generating summary report...")
    report_path = generate_report(
        output_dir, csv_path, overview, missing_table, num_desc, cat_desc,
        corr_pairs, skew_kurt, outlier_summary, tsne_note, datetime_cols, period_stats_df
    )

    print(f"\nDone. All outputs saved in: {os.path.abspath(output_dir)}")
    print(f"Summary report: {report_path}")
    return output_dir


if __name__ == "__main__":
    if INPUT_CSV_PATH:
        # Hardcoded path set above -> run directly, no CLI args needed.
        run_eda(INPUT_CSV_PATH, OUTPUT_DIR)
    else:
        # Fall back to command-line usage: python eda_report.py <csv> [output_dir]
        if len(sys.argv) < 2:
            print("Usage: python eda_report.py <path_to_csv> [output_dir]")
            sys.exit(1)
        csv_arg = sys.argv[1]
        out_arg = sys.argv[2] if len(sys.argv) > 2 else "eda_output"
        run_eda(csv_arg, out_arg)
