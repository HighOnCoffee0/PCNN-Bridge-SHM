import pandas as pd

input_file = r"C:\Users\sriha\Desktop\College\Project\Maths_P\CSV\train.csv"
output_file = r"C:\Users\sriha\Desktop\College\Project\Maths_P\Final EDA\train_for_eda.csv"

df = pd.read_csv(input_file)

# keep Timestamp, the raw physical-unit columns, and the two time-cycle
# features (hour_sin/hour_cos are genuinely new information, not a
# duplicate of anything else, so they're worth keeping in for EDA)
keep_cols = [
    'Timestamp',
    'Vehicle_Load_tons', 'Temperature_C', 'Vibration_ms2',
    'Strain_microstrain', 'Cable_Member_Tension_kN', 'Structural_Health_Index_SHI',
    'hour_sin', 'hour_cos',
]
df[keep_cols].to_csv(output_file, index=False)
print(f"Saved clean EDA-ready file: {output_file} ({len(df)} rows, {len(keep_cols)} columns)")