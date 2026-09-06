"""
Day 57: exploratory look at the Week 8 dataset before any ML work starts.

No synthetic-data fallback -- if the real CSV is missing, this is a setup
problem (wrong path, forgot to copy to Drive) that should be fixed, not
papered over with fabricated numbers. That would undo the no-fake-data
discipline enforced in Days 55-56.

Run with:
    python ml_foundations.py
"""
import pandas as pd

CSV_PATH = "/content/drive/MyDrive/SMR-AI-DigitalTwin/smr_neutronics_dataset.csv"
# Adjust if your CSV lives somewhere else in Drive.

try:
    data = pd.read_csv(CSV_PATH)
except FileNotFoundError:
    raise FileNotFoundError(
        f"Real dataset not found at {CSV_PATH}. This project trains only "
        "on real OpenMC sweep output -- check the path above, or rerun "
        "build_dataset.py if the CSV was never saved to Drive."
    )

print(f"Dataset loaded: {len(data)} rows.\n")
print(data.describe())

print("\n--- Feature variation check ---")
for col in ["control_rod_height_cm", "enrichment", "pin_pitch_cm"]:
    n_unique = data[col].nunique()
    print(f"  {col}: {n_unique} unique values -> {sorted(data[col].unique())}")
    if n_unique < 2:
        print(f"    WARNING: {col} does not vary -- a model can't learn a "
              f"relationship it never sees change.")

print(f"\nk_effective_mean range: {data['k_effective_mean'].min():.4f} "
      f"to {data['k_effective_mean'].max():.4f}")

if "k_effective_std" in data.columns:
    print(f"k_effective_std range: {data['k_effective_std'].min():.5f} "
          f"to {data['k_effective_std'].max():.5f}")
    print("(Useful later: rows with unusually high std could be weighted "
          "down or flagged, since the surrogate should trust noisier "
          "OpenMC estimates less.)")
