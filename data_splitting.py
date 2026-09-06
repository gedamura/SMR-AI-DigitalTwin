"""
Day 58: isolates inputs (X) from target (y) and splits into an 80% training
set / 20% test set.

Uses all three physical parameters as features -- control_rod_height_cm
alone can't explain k-eff variation driven by enrichment or pitch, both of
which showed strong, statistically significant effects in Day 51
(~29 sigma and ~65 sigma respectively).

Run with:
    python data_splitting.py
"""
import pandas as pd
from sklearn.model_selection import train_test_split

CSV_PATH = "/content/drive/MyDrive/SMR-AI-DigitalTwin/smr_neutronics_dataset.csv"
df = pd.read_csv(CSV_PATH)

FEATURE_COLUMNS = ["control_rod_height_cm", "enrichment", "pin_pitch_cm"]
TARGET_COLUMN = "k_effective_mean"

X = df[FEATURE_COLUMNS]
y = df[TARGET_COLUMN]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

print(f"Total rows: {len(df)}")
print(f"Training set: {X_train.shape[0]} rows x {X_train.shape[1]} features")
print(f"Test set:     {X_test.shape[0]} rows x {X_test.shape[1]} features")

print("\n--- Training set feature ranges ---")
print(X_train.describe())

print("\n--- Test set coverage check ---")
# With only 18 test rows split across 3 enrichments x 3 pitches x 10 rod
# heights, worth confirming the test set isn't accidentally missing a whole
# enrichment or pitch level -- that would make Day 61's metrics less
# meaningful for the parameter ranges the model never got tested against.
for col in ["enrichment", "pin_pitch_cm"]:
    print(f"\n{col} value counts in test set:")
    print(X_test[col].value_counts().sort_index())
