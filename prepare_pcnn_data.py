import pandas as pd
import numpy as np
import json

# ============================================================
# 0. LOAD + PARSE
# ============================================================
input_file = r"C:\Users\sriha\Desktop\College\Project\Maths_P\CSV\Main_interpolated.csv"
df = pd.read_csv(input_file)
df['Timestamp'] = pd.to_datetime(df['Timestamp'], format="%d-%m-%Y %H:%M")
df = df.sort_values('Timestamp').reset_index(drop=True)

# ============================================================
# 1. CHRONOLOGICAL SPLIT — 20 / 5 / 5 days, by calendar day boundary
#    (never shuffle time-series data before splitting)
# ============================================================
start_date = df['Timestamp'].min().normalize()
train_end   = start_date + pd.Timedelta(days=20)   # end of day 20 (exclusive)
val_end     = start_date + pd.Timedelta(days=25)   # end of day 25 (exclusive)
# remaining 5 days -> test

train_df = df[df['Timestamp'] < train_end].reset_index(drop=True)
val_df   = df[(df['Timestamp'] >= train_end) & (df['Timestamp'] < val_end)].reset_index(drop=True)
test_df  = df[df['Timestamp'] >= val_end].reset_index(drop=True)

print(f"Train: {len(train_df)} rows  ({train_df['Timestamp'].min()} -> {train_df['Timestamp'].max()})")
print(f"Val:   {len(val_df)} rows  ({val_df['Timestamp'].min()} -> {val_df['Timestamp'].max()})")
print(f"Test:  {len(test_df)} rows  ({test_df['Timestamp'].min()} -> {test_df['Timestamp'].max()})")

# ============================================================
# 1b. ENCODE TIME — split into "slow drift" and "daily cycle"
# ============================================================
def add_time_features(split_df, reference_start):
    out = split_df.copy()
    # slow drift: elapsed time since the very start of TRAINING data
    out['elapsed_seconds'] = (out['Timestamp'] - reference_start).dt.total_seconds()
    # daily cycle: hour-of-day as an angle, wrapped via sin/cos so
    # 23:59 and 00:00 end up close together instead of far apart
    hour_frac = out['Timestamp'].dt.hour + out['Timestamp'].dt.minute / 60.0
    angle = 2 * np.pi * (hour_frac / 24.0)
    out['hour_sin'] = np.sin(angle)
    out['hour_cos'] = np.cos(angle)
    return out

reference_start = train_df['Timestamp'].min()   # anchor elapsed time to training start
train_df = add_time_features(train_df, reference_start)
val_df   = add_time_features(val_df, reference_start)
test_df  = add_time_features(test_df, reference_start)

# ============================================================
# 2. FIT NORMALIZATION ON TRAIN ONLY (z-score / standard scaling)
# ============================================================
feature_cols = [
    'Vehicle_Load_tons', 'Temperature_C', 'Vibration_ms2',        # inputs
    'Strain_microstrain', 'Cable_Member_Tension_kN',              # outputs w/ physics residual
    'Structural_Health_Index_SHI',                                # plain supervised output
    'elapsed_seconds',                                            # time input (slow-drift component)
]
# hour_sin / hour_cos are NOT z-scored — they're already bounded
# in [-1, 1] by construction, and scaling them further would
# distort the cyclical shape they're designed to preserve

stats = {}
for col in feature_cols:
    mean = train_df[col].mean()
    std = train_df[col].std()
    stats[col] = {'mean': float(mean), 'std': float(std)}

# save stats so the SAME transform can be reapplied later (e.g. at inference)
with open(r"C:\Users\sriha\Desktop\College\Project\Maths_P\CSV\normalization_stats.json", "w") as f:
    json.dump(stats, f, indent=2)

print("\nNormalization stats (fit on training set only):")
for col, s in stats.items():
    print(f"  {col}: mean={s['mean']:.4f}, std={s['std']:.4f}")

# ============================================================
# 3. APPLY THE SAME TRANSFORM TO ALL THREE SPLITS
# ============================================================
def normalize(split_df, stats, cols):
    out = split_df.copy()
    for col in cols:
        out[col + '_norm'] = (out[col] - stats[col]['mean']) / stats[col]['std']
    return out

train_df = normalize(train_df, stats, feature_cols)
val_df   = normalize(val_df, stats, feature_cols)
test_df  = normalize(test_df, stats, feature_cols)

# ============================================================
# 4. SAVE SPLITS
# ============================================================
out_dir = r"C:\Users\sriha\Desktop\College\Project\Maths_P\CSV"
train_df.to_csv(f"{out_dir}\\train.csv", index=False)
val_df.to_csv(f"{out_dir}\\val.csv", index=False)
test_df.to_csv(f"{out_dir}\\test.csv", index=False)

print(f"\nSaved: train.csv ({len(train_df)}), val.csv ({len(val_df)}), test.csv ({len(test_df)})")
print(f"Saved normalization stats to normalization_stats.json")
print("\nFinal backbone input columns to feed the model:")
print("  Vehicle_Load_tons_norm, Temperature_C_norm, Vibration_ms2_norm,")
print("  elapsed_seconds_norm, hour_sin, hour_cos")

# ============================================================
# 5. HOW TO DE-NORMALIZE INSIDE THE PHYSICS LOSS (reference only)
# ============================================================
# Example, in your training loop (PyTorch), using the saved stats:
#
#   load_mean, load_std = stats['Vehicle_Load_tons']['mean'], stats['Vehicle_Load_tons']['std']
#   tension_mean, tension_std = stats['Cable_Member_Tension_kN']['mean'], stats['Cable_Member_Tension_kN']['std']
#
#   # model works in normalized space:
#   load_norm = batch['Vehicle_Load_tons_norm']
#   tension_pred_norm = model.tension_head(backbone_features)
#
#   # de-normalize BEFORE computing the physics residual, so k_hat stays
#   # in real physical units (kN per ton), matching your earlier regression:
#   load_real = load_norm * load_std + load_mean
#   tension_pred_real = tension_pred_norm * tension_std + tension_mean
#
#   expected_tension_real = k_hat * load_real + b1_hat
#   residual = tension_pred_real - expected_tension_real
#   physics_loss_tension = torch.mean(residual ** 2)

# ============================================================
# 6. DE-NORMALIZING TIME (reference only — for plotting/reporting,
#    not for a physics equation, since none of your residuals use Time)
# ============================================================
# elapsed_seconds needs the same de-normalize formula as everything else:
#
#   elapsed_mean = stats['elapsed_seconds']['mean']
#   elapsed_std  = stats['elapsed_seconds']['std']
#   elapsed_seconds_real = elapsed_seconds_norm * elapsed_std + elapsed_mean
#
#   # convert back to an actual timestamp for plotting, using the same
#   # reference_start anchor point saved during preprocessing:
#   actual_timestamp = reference_start + pd.to_timedelta(elapsed_seconds_real, unit='s')
#
# hour_sin / hour_cos need NO de-normalization step (they were never
# normalized to begin with — see earlier explanation). If you want the
# actual hour-of-day back for a label or plot axis, recover it directly
# from the angle instead:
#
#   import numpy as np
#   angle = np.arctan2(hour_sin, hour_cos)          # radians, range -pi..pi
#   angle = (angle + 2*np.pi) % (2*np.pi)            # shift into 0..2pi
#   hour_of_day = angle / (2*np.pi) * 24             # convert to 0..24 hours
