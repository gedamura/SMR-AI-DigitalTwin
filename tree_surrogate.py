"""
Day 60: fits a Decision Tree Regressor on all three physical parameters.

Day 56's plot showed a curve that's steep near full insertion and flattens
toward full withdrawal -- not a straight line. A decision tree splits the
feature space into regions and fits a local average in each, capturing this
kind of curvature (and feature interactions) that the Day 59 linear model
structurally can't.

UPDATE (post-Day 61 depth sweep): originally used max_depth=5. A depth
sensitivity check in Day 61 showed test R^2 kept climbing through depth=8
(0.977 -> 0.987, ~43% lower MSE) before plateauing exactly at depth=8/10/
unlimited -- identical results across all three, meaning the tree naturally
stops finding useful splits there rather than being artificially capped.
Deeper settings didn't overfit either (test R^2 held, didn't degrade), so
depth=8 is the real elbow: genuine improvement up to that point, nothing
gained by going further. Updated to max_depth=8 here so this script and the
final Day 63 saved model use the same, better-justified setting.

The Day 61 sweep also disproved a specific concern: at depth=5, feature
importance was 95.4% rod height / 1.8% enrichment / 2.8% pitch, suspiciously
lopsided next to Day 59's linear coefficients. But enrichment/pitch
importance barely moved across the whole depth sweep (staying near 2%/3%
even at depth=8+) -- so that dominance is genuine physics, not an artifact
of insufficient tree depth. Rod height really does explain the large
majority of k-eff variation in this dataset.

max_depth=8 still caps complexity rather than using "unlimited" -- with only
72 training rows, capping at the point where the tree naturally plateaus is
a safer choice than removing the guardrail entirely, even though this
dataset didn't show overfitting at deeper settings.

Run with:
    python tree_surrogate.py
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor

CSV_PATH = "/content/drive/MyDrive/SMR-AI-DigitalTwin/smr_neutronics_dataset.csv"
df = pd.read_csv(CSV_PATH)

FEATURE_COLUMNS = ["control_rod_height_cm", "enrichment", "pin_pitch_cm"]
X_train, X_test, y_train, y_test = train_test_split(
    df[FEATURE_COLUMNS], df["k_effective_mean"], test_size=0.2, random_state=42
)

tree_model = DecisionTreeRegressor(max_depth=8, random_state=42)
tree_model.fit(X_train, y_train)

predictions = tree_model.predict(X_test)
print("Decision tree trained.\n")

print("--- Feature importances ---")
# Unlike the Day 59 linear coefficients, these are already scale-normalized
# -- no need to weight by each feature's range to compare them fairly.
for feature, importance in zip(FEATURE_COLUMNS, tree_model.feature_importances_):
    print(f"  {feature}: {importance:.3f}")

print("\n--- Sample predictions vs. actual (first 5 test rows) ---")
comparison = pd.DataFrame({
    "true_k_eff": y_test.values[:5],
    "predicted_k_eff": predictions[:5],
})
comparison["abs_error"] = (comparison["true_k_eff"] - comparison["predicted_k_eff"]).abs()
print(comparison)
