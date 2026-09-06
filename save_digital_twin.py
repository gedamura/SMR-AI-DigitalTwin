"""
Day 63: trains the final surrogate on the full dataset and saves it to disk
with joblib, so it can be reloaded instantly without retraining.

Final model choice: DecisionTreeRegressor(max_depth=8), selected in Day 61's
depth sensitivity sweep (best test R^2=0.987 before the plateau) and
confirmed in a follow-up comparison against a log-featured linear model
(R^2=0.963) -- the tree captures real accuracy beyond what a single log
transform explains, likely interaction effects between rod height and
enrichment/pitch that a purely additive model can't reach.

Trains on the FULL dataset (train+test combined) for this final artifact --
standard practice once performance has already been validated on a held-out
split, to use all 90 rows for the deployed model rather than leaving 18
unused.

Saves a metadata JSON alongside the model recording feature order and
target, so anything loading the .pkl later doesn't have to guess the
expected input shape.

Run with:
    python save_digital_twin.py
"""
import pandas as pd
import json
from sklearn.tree import DecisionTreeRegressor
import joblib

CSV_PATH = "/content/drive/MyDrive/SMR-AI-DigitalTwin/smr_neutronics_dataset.csv"
OUTPUT_DIR = "/content/drive/MyDrive/SMR-AI-DigitalTwin"

df = pd.read_csv(CSV_PATH)

FEATURE_COLUMNS = ["control_rod_height_cm", "enrichment", "pin_pitch_cm"]
TARGET_COLUMN = "k_effective_mean"

X = df[FEATURE_COLUMNS]
y = df[TARGET_COLUMN]

digital_twin_brain = DecisionTreeRegressor(max_depth=8, random_state=42)
digital_twin_brain.fit(X, y)

model_path = f"{OUTPUT_DIR}/smr_digital_twin_model.pkl"
joblib.dump(digital_twin_brain, model_path)

metadata = {
    "feature_columns": FEATURE_COLUMNS,
    "target_column": TARGET_COLUMN,
    "model_type": "DecisionTreeRegressor",
    "max_depth": 8,
    "trained_on_n_rows": len(df),
    "held_out_test_r2": 0.9868,
    "held_out_test_mse": 2.052701e-03,
    "model_selection_notes": (
        "max_depth chosen via sensitivity sweep over [3, 5, 8, 10, None]; "
        "R^2 plateaued at depth=8 (identical results through 'unlimited'), "
        "so 8 was chosen as the natural elbow rather than an arbitrary cap. "
        "Compared against a log-featured linear regression alternative "
        "(R^2=0.9633) -- tree retained for higher accuracy, though the "
        "log-linear result confirms the underlying rod-height response is "
        "genuinely log-shaped, which the tree approximates via flat "
        "segments rather than a smooth curve."
    ),
}
with open(f"{OUTPUT_DIR}/smr_digital_twin_model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Model saved to:    {model_path}")
print(f"Metadata saved to: {OUTPUT_DIR}/smr_digital_twin_model_metadata.json")
print(f"\nTrained on {len(df)} rows, features: {FEATURE_COLUMNS}")

# Quick reload check: confirms the saved file actually works before you
# consider Day 63 done, rather than assuming joblib.dump succeeded silently.
reloaded = joblib.load(model_path)
sample_pred = reloaded.predict(X.iloc[[0]])
print(f"\nReload check: model loads correctly, sample prediction = {sample_pred[0]:.5f} "
      f"(vs. true k_eff = {y.iloc[0]:.5f} for that row)")
