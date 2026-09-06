"""
Day 62: visual comparison of surrogate predictions against true OpenMC data.

With 3 input features, a single line plot against one feature can't fully
represent the model anymore -- predictions depend on all three inputs at
once. Two complementary plots instead:
  1. Parity plot (predicted vs. true, on the held-out test set) -- the real
     accuracy check, works regardless of feature count.
  2. Sliced line plot at fixed baseline enrichment/pitch -- for visual
     continuity with Day 56's sweep validation plot and physical intuition
     about the rod-height response curve.

Uses max_depth=8, the depth chosen in Day 61's sensitivity sweep (best test
R^2 = 0.987, before the plateau -- see tree_surrogate.py for the full
reasoning).

Run with:
    python plot_predictions.py
(In Colab, plots render inline automatically.)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import r2_score

CSV_PATH = "/content/drive/MyDrive/SMR-AI-DigitalTwin/smr_neutronics_dataset.csv"
OUTPUT_DIR = "/content/drive/MyDrive/SMR-AI-DigitalTwin"

df = pd.read_csv(CSV_PATH)

FEATURE_COLUMNS = ["control_rod_height_cm", "enrichment", "pin_pitch_cm"]
X_train, X_test, y_train, y_test = train_test_split(
    df[FEATURE_COLUMNS], df["k_effective_mean"], test_size=0.2, random_state=42
)

model = DecisionTreeRegressor(max_depth=8, random_state=42).fit(X_train, y_train)
y_pred_test = model.predict(X_test)
test_r2 = r2_score(y_test, y_pred_test)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# --- Panel 1: parity plot ---
ax1.scatter(y_test, y_pred_test, alpha=0.7, color="#2b6cb0", s=60,
            edgecolors="white", linewidth=0.5)
lims = [min(y_test.min(), y_pred_test.min()) - 0.03,
        max(y_test.max(), y_pred_test.max()) + 0.03]
ax1.plot(lims, lims, 'k--', alpha=0.5, label="Perfect prediction")
ax1.set_xlim(lims)
ax1.set_ylim(lims)
ax1.set_xlabel("True k-effective (OpenMC)")
ax1.set_ylabel("Predicted k-effective (surrogate)")
ax1.set_title(f"Parity plot: predicted vs. true (test set, R\u00b2={test_r2:.3f})")
ax1.legend()
ax1.grid(alpha=0.3)

# --- Panel 2: sliced line plot at baseline enrichment/pitch ---
BASELINE_ENRICHMENT = 0.045
BASELINE_PITCH = 1.26
plot_heights = np.linspace(0, 60, 300)
plot_X = pd.DataFrame({
    "control_rod_height_cm": plot_heights,
    "enrichment": BASELINE_ENRICHMENT,
    "pin_pitch_cm": BASELINE_PITCH,
})
plot_y = model.predict(plot_X)

baseline_data = df[
    (df["enrichment"] == BASELINE_ENRICHMENT) & (df["pin_pitch_cm"] == BASELINE_PITCH)
]
ax2.scatter(baseline_data["control_rod_height_cm"], baseline_data["k_effective_mean"],
            color="#e53e3e", s=70, zorder=3, label="True OpenMC data (baseline config)")
ax2.plot(plot_heights, plot_y, color="#2b6cb0", linewidth=2.0,
          label="Surrogate prediction (baseline config)")
ax2.set_xlabel("Control rod height (cm)")
ax2.set_ylabel("k-effective")
ax2.set_title(f"Surrogate vs. true, at enrichment={BASELINE_ENRICHMENT}, pitch={BASELINE_PITCH}")
ax2.legend()
ax2.grid(alpha=0.3)

plt.tight_layout()
fig.savefig(f"{OUTPUT_DIR}/surrogate_accuracy.png", dpi=150)
plt.show()

print(f"Test R\u00b2: {test_r2:.4f}")
print(f"Saved plot to: {OUTPUT_DIR}/surrogate_accuracy.png")

# Note on panel 2: the "staircase" look you may see in the blue prediction
# line is expected -- a decision tree predicts a constant value within each
# leaf region, so its output is piecewise-flat rather than smoothly curved,
# even though the true physics (red points) follows a smooth trend. This
# isn't an error; it's an inherent visual signature of tree-based models,
# worth being able to explain if asked about it.
