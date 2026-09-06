"""
Day 61: formal statistical evaluation of both surrogate models.

MSE = average squared prediction error (lower is better).
R^2 = fraction of target variance explained by the model (1.0 = perfect).

With 90 total rows and an 18-row test set, treat these as a first read
rather than a tight confidence interval -- small test sets produce noisier
metric estimates than a dataset with thousands of rows would.

Includes a max_depth sensitivity sweep for the tree model, prompted by Day
60's result: at depth=5, feature importance came back 95.4% rod height /
1.8% enrichment / 2.8% pitch -- much more lopsided than the roughly
comparable range-weighted contributions the Day 59 linear coefficients
implied. This could mean rod height genuinely dominates, or it could mean
depth=5 ran out of splits before meaningfully using enrichment/pitch. This
sweep answers that with numbers instead of a guess, before any model gets
saved as the final deliverable in Day 63.

Run with:
    python evaluate_surrogate.py
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error, r2_score

CSV_PATH = "/content/drive/MyDrive/SMR-AI-DigitalTwin/smr_neutronics_dataset.csv"
df = pd.read_csv(CSV_PATH)

FEATURE_COLUMNS = ["control_rod_height_cm", "enrichment", "pin_pitch_cm"]
X_train, X_test, y_train, y_test = train_test_split(
    df[FEATURE_COLUMNS], df["k_effective_mean"], test_size=0.2, random_state=42
)

print("--- Linear vs. Tree (depth=8, chosen via depth sweep below) ---")
models = {
    "Linear Regression": LinearRegression(),
    "Decision Tree (depth=8)": DecisionTreeRegressor(max_depth=8, random_state=42),
}
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"{name}:")
    print(f"  MSE: {mse:.6e}")
    print(f"  R^2: {r2:.4f}  (1.00 = perfect)")

print("\n--- Tree depth sensitivity sweep ---")
print("Checking whether shallower depths under-serve enrichment/pitch, or")
print("whether rod height genuinely dominates regardless of depth.")
print("(Result from a prior run of this sweep: R^2 climbed 0.954->0.977->0.987")
print("through depth=3/5/8, then plateaued exactly at 8/10/unlimited. Chose")
print("max_depth=8 above as the real elbow -- genuine improvement up to")
print("that point, nothing gained by going further.)\n")

depth_results = []
for depth in [3, 5, 8, 10, None]:  # None = unlimited depth
    tree = DecisionTreeRegressor(max_depth=depth, random_state=42)
    tree.fit(X_train, y_train)
    y_pred = tree.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    importances = dict(zip(FEATURE_COLUMNS, tree.feature_importances_))
    depth_results.append({
        "max_depth": depth if depth is not None else "unlimited",
        "test_R2": r2,
        "test_MSE": mse,
        "rod_height_importance": importances["control_rod_height_cm"],
        "enrichment_importance": importances["enrichment"],
        "pitch_importance": importances["pin_pitch_cm"],
    })

depth_df = pd.DataFrame(depth_results)
print(depth_df.to_string(index=False))

print("\nInterpretation guide:")
print("  - If R^2 keeps improving as depth increases: depth=5 was leaving")
print("    accuracy on the table, and a deeper tree is worth adopting.")
print("  - If R^2 plateaus or gets WORSE at higher depth (with only 72")
print("    training rows, this is a real overfitting risk): depth=5 was")
print("    a reasonable choice, and rod height's dominance in importance")
print("    is likely a genuine reflection of its outsized effect on k-eff,")
print("    not an artifact of insufficient depth.")
print("  - Watch enrichment/pitch importance across the sweep too -- if")
print("    they rise substantially at deeper levels without R^2 dropping,")
print("    that's a sign the shallow tree really was under-using them.")
