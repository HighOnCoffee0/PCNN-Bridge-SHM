import pandas as pd
import numpy as np
import json
from sklearn.linear_model import LinearRegression

# ============================================================
# 0. LOAD TRAINING DATA (real units — NOT the _norm columns)
# ============================================================
csv_folder = r"C:\Users\sriha\Desktop\College\Project\Maths_P\CSV"
train = pd.read_csv(f"{csv_folder}\\train.csv")

# ============================================================
# 1. EQUATION 1 — Cable Tension = k_hat * Load + b1_hat
# ============================================================
X_tension = train[['Vehicle_Load_tons']]
y_tension = train['Cable_Member_Tension_kN']

model_tension = LinearRegression().fit(X_tension, y_tension)
k_hat = float(model_tension.coef_[0])
b1_hat = float(model_tension.intercept_)
r2_tension = model_tension.score(X_tension, y_tension)

print("=== Equation 1: Cable Tension ===")
print(f"Tension = {k_hat:.6f} * Load + {b1_hat:.6f}")
print(f"R² = {r2_tension:.4f}")
print()

# ============================================================
# 2. EQUATION 2 — Strain = c1_hat*Load + c2_hat*Load^2 + c3_hat*Vibration + b2_hat
# ============================================================
train['Load_sq'] = train['Vehicle_Load_tons'] ** 2

X_strain = train[['Vehicle_Load_tons', 'Load_sq', 'Vibration_ms2']]
y_strain = train['Strain_microstrain']

model_strain = LinearRegression().fit(X_strain, y_strain)
c1_hat, c2_hat, c3_hat = [float(c) for c in model_strain.coef_]
b2_hat = float(model_strain.intercept_)
r2_strain = model_strain.score(X_strain, y_strain)

print("=== Equation 2: Strain ===")
print(f"Strain = {c1_hat:.6f}*Load + {c2_hat:.6f}*Load^2 + {c3_hat:.6f}*Vibration + {b2_hat:.6f}")
print(f"R² = {r2_strain:.4f}")
print()

# ============================================================
# 3. SANITY CHECK — compare against earlier findings in this project
# ============================================================
print("=== Sanity check against earlier investigation ===")
print(f"Tension R² expected ~0.96, got {r2_tension:.4f}  {'OK' if abs(r2_tension - 0.96) < 0.02 else 'CHECK THIS'}")
print(f"Strain R² expected ~0.888, got {r2_strain:.4f}  {'OK' if abs(r2_strain - 0.888) < 0.02 else 'CHECK THIS'}")
print()

# ============================================================
# 4. SAVE COEFFICIENTS — used later to initialize the PyTorch model
# ============================================================
coefficients = {
    "tension": {
        "k_hat": k_hat,
        "b1_hat": b1_hat,
        "r2": r2_tension,
    },
    "strain": {
        "c1_hat": c1_hat,
        "c2_hat": c2_hat,
        "c3_hat": c3_hat,
        "b2_hat": b2_hat,
        "r2": r2_strain,
    },
}

out_path = f"{csv_folder}\\physics_coefficients.json"
with open(out_path, "w") as f:
    json.dump(coefficients, f, indent=2)

print(f"Saved coefficients to: {out_path}")
