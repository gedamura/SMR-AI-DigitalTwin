"""
Day 59: fits a Linear Regression baseline on all three physical parameters.

With three features, the model fits a hyperplane:
    k_eff = m1*rod_height + m2*enrichment + m3*pitch + b
Each coefficient tells you how much k-eff moves per unit change in that
parameter, holding the others fixed. This is the baseline model -- fast and
interpretable, but only as good as the real relationship's linearity. Day 56's
plot already showed the rod-height curve isn't perfectly linear (it flattens
toward full withdrawal), so don't expect a perfect fit here -- that's exactly
what Day 60's tree model is for.

Run with:
    python linear_surrogate.py
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

CSV_PATH = "/content/drive/MyDrive/SMR-AI-DigitalTwin/smr_neutronics_dataset.csv"
df = pd.read_csv(CSV_PATH)

FEATURE_COLUMNS = ["control_rod_height_cm", "enrichment", "pin_pitch_cm"]
X_train, X_test, y_train, y_test = train_test_split(
    df[FEATURE_COLUMNS], df["k_effective_mean"], test_size=0.2, random_state=42
)

linear_model = LinearRegression()
linear_model.fit(X_train, y_train)

print("Linear model trained.\n")
for feature, coef in zip(FEATURE_COLUMNS, linear_model.coef_):
    print(f"  Coefficient for {feature}: {coef:.6f}")
print(f"  Intercept: {linear_model.intercept_:.6f}")

print("\n--- Sign sanity check against Day 51/56 findings ---")
signs = dict(zip(FEATURE_COLUMNS, linear_model.coef_))
checks = [
    ("control_rod_height_cm", "positive", signs["control_rod_height_cm"] > 0,
     "more withdrawn (higher rod height) should raise k-eff"),
    ("enrichment", "positive", signs["enrichment"] > 0,
     "more U-235 should raise k-eff"),
    ("pin_pitch_cm", "positive", signs["pin_pitch_cm"] > 0,
     "in this under-moderated regime, wider pitch raised k-eff in Day 56's plot"),
]
for feature, expected, passed, reason in checks:
    status = "OK" if passed else "UNEXPECTED"
    print(f"  [{status}] {feature}: expected {expected} -- {reason}")
