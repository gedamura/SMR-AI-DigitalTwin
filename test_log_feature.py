"""
Bonus comparison, prompted by an observation on Day 62's sliced plot: the
tree's stair-step curve looked like it might be approximating an underlying
log-shaped (diminishing-returns) relationship between rod height and k-eff.

A decision tree can only ever output flat segments -- that's a structural
property of the model family, not a fitting failure, and doesn't mean the
underlying physics isn't smooth. This script tests a smooth alternative
directly: linear regression, but with log(rod_height + 1) as an engineered
feature instead of raw rod height. (+1 avoids log(0) at full insertion.)
Enrichment and pitch stay untransformed -- nothing in the Day 51/56 data
suggested a non-linear relationship for those two.

If this log-featured model matches or beats the tree's R^2 while producing
a smooth, physically motivated curve, it may be a better choice for Day 63's
final saved model -- both more defensible (matches expected reactor physics
shape) and free of the tree's flat-segment artifact. If it falls short, the
tree's higher accuracy is worth keeping despite the visual blockiness.

Run with:
    python test_log_feature.py
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error, r2_score

CSV_PATH = "/content/drive/MyDrive/SMR-AI-DigitalTwin/smr_neutronics_dataset.csv"
OUTPUT_DIR = "/content/drive/MyDrive/SMR-AI-DigitalTwin"

df = pd.read_csv(CSV_PATH)

# Engineer the log feature, keep enrichment/pitch as-is.
df["log_rod_height"] = np.log(df["control_rod_height_cm"] + 1)

FEATURE_COLUMNS_LOG = ["log_rod_height", "enrichment", "pin_pitch_cm"]
FEATURE_COLUMNS_RAW = ["control_rod_height_cm", "enrichment", "pin_pitch_cm"]

# Same random_state/split as every prior script -- same rows in train/test
# throughout, so this is a fair apples-to-apples comparison against Day 61.
X_train_log, X_test_log, y_train, y_test = train_test_split(
    df[FEATURE_COLUMNS_LOG], df["k_effective_mean"], test_size=0.2, random_state=42
)
X_train_raw, X_test_raw, _, _ = train_test_split(
    df[FEATURE_COLUMNS_RAW], df["k_effective_mean"], test_size=0.2, random_state=42
)

log_linear = LinearRegression().fit(X_train_log, y_train)
tree = DecisionTreeRegressor(max_depth=8, random_state=42).fit(X_train_raw, y_train)

y_pred_log = log_linear.predict(X_test_log)
y_pred_tree = tree.predict(X_test_raw)

print("--- Log-featured linear regression vs. depth=8 tree ---")
print(f"Log-linear:  MSE={mean_squared_error(y_test, y_pred_log):.6e}  "
      f"R^2={r2_score(y_test, y_pred_log):.4f}")
print(f"Tree(d=8):   MSE={mean_squared_error(y_test, y_pred_tree):.6e}  "
      f"R^2={r2_score(y_test, y_pred_tree):.4f}")

print(f"\nLog-linear coefficients:")
for feature, coef in zip(FEATURE_COLUMNS_LOG, log_linear.coef_):
    print(f"  {feature}: {coef:.6f}")
print(f"  Intercept: {log_linear.intercept_:.6f}")

# --- Visual comparison at baseline enrichment/pitch ---
BASELINE_ENRICHMENT = 0.045
BASELINE_PITCH = 1.26
plot_heights = np.linspace(0, 60, 300)

plot_X_log = pd.DataFrame({
    "log_rod_height": np.log(plot_heights + 1),
    "enrichment": BASELINE_ENRICHMENT,
    "pin_pitch_cm": BASELINE_PITCH,
})
plot_X_raw = pd.DataFrame({
    "control_rod_height_cm": plot_heights,
    "enrichment": BASELINE_ENRICHMENT,
    "pin_pitch_cm": BASELINE_PITCH,
})

fig, ax = plt.subplots(figsize=(8, 5))
baseline_data = df[
    (df["enrichment"] == BASELINE_ENRICHMENT) & (df["pin_pitch_cm"] == BASELINE_PITCH)
]
ax.scatter(baseline_data["control_rod_height_cm"], baseline_data["k_effective_mean"],
           color="#e53e3e", s=70, zorder=3, label="True OpenMC data")
ax.plot(plot_heights, log_linear.predict(plot_X_log), color="#38a169",
        linewidth=2.0, label="Log-linear prediction")
ax.plot(plot_heights, tree.predict(plot_X_raw), color="#2b6cb0",
        linewidth=2.0, linestyle="--", label="Tree (depth=8) prediction")
ax.set_xlabel("Control rod height (cm)")
ax.set_ylabel("k-effective")
ax.set_title(f"Log-linear vs. tree, at enrichment={BASELINE_ENRICHMENT}, pitch={BASELINE_PITCH}")
ax.legend()
ax.grid(alpha=0.3)
fig.savefig(f"{OUTPUT_DIR}/log_vs_tree_comparison.png", dpi=150)
plt.show()

print(f"\nSaved comparison plot to: {OUTPUT_DIR}/log_vs_tree_comparison.png")
