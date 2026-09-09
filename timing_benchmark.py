"""
Timing benchmark: surrogate model prediction speed vs. a full OpenMC run.

Measures two things fairly:
1. Surrogate prediction time -- averaged over many calls, since a single
   .predict() call's wall time is dominated by Python/sklearn overhead,
   not the actual tree traversal. Averaging gives a stable per-call number.
2. Full OpenMC run time -- using the actual settings from run_sweep.py
   (batches=30, inactive=5, particles=1000), the real settings used to
   generate this project's dataset. Includes geometry/materials/settings
   compilation, since a genuinely new (rod_height, enrichment, pitch)
   config can't skip that step -- this is the real wall-clock cost of
   getting a k-eff value for an arbitrary new configuration via simulation.

Run with:
    python timing_benchmark.py
"""
import time
import glob
import os

import joblib
import pandas as pd

MODEL_PATH = "/content/drive/MyDrive/SMR-AI-DigitalTwin/smr_digital_twin_model.pkl"

# --- Part 1: surrogate prediction speed ---
model = joblib.load(MODEL_PATH)

test_input = pd.DataFrame({
    "control_rod_height_cm": [30.0],
    "enrichment": [0.045],
    "pin_pitch_cm": [1.26],
})

N_CALLS = 10000
start = time.perf_counter()
for _ in range(N_CALLS):
    model.predict(test_input)
elapsed = time.perf_counter() - start

surrogate_ms_per_call = (elapsed / N_CALLS) * 1000
print(f"Surrogate: {N_CALLS} predictions in {elapsed:.4f} sec")
print(f"Surrogate: {surrogate_ms_per_call:.5f} ms per prediction (averaged)\n")

# --- Part 2: full OpenMC run, same settings as run_sweep.py ---
DATA_DIR = "/content/drive/MyDrive/openmc_data"
matches = glob.glob(os.path.join(DATA_DIR, "**", "cross_sections.xml"), recursive=True)
if not matches:
    raise FileNotFoundError(f"No cross_sections.xml found under {DATA_DIR}.")
os.environ["OPENMC_CROSS_SECTIONS"] = matches[0]

import openmc
openmc.config['cross_sections'] = matches[0]

from build_geometry import compile_reactor_core
from build_settings import build_settings

CORE_TOP = 60.0
build_settings(batches=30, inactive=5, particles=1000, core_top=CORE_TOP)

# Clear any leftover statepoint before timing, so glob finds exactly one.
for f in glob.glob("statepoint.*.h5"):
    os.remove(f)

start = time.perf_counter()
compile_reactor_core(control_rod_height=30.0, enrichment=0.045, pin_pitch=1.26, core_top=CORE_TOP)
openmc.run(output=False)
openmc_elapsed = time.perf_counter() - start

print(f"\nFull OpenMC run (sweep settings, batches=30/inactive=5/particles=1000): "
      f"{openmc_elapsed:.3f} sec")

# --- Comparison ---
speedup = (openmc_elapsed * 1000) / surrogate_ms_per_call
print(f"\n--- Comparison ---")
print(f"Surrogate:  {surrogate_ms_per_call:.5f} ms")
print(f"OpenMC:     {openmc_elapsed*1000:.1f} ms  ({openmc_elapsed:.3f} sec)")
print(f"Speedup:    ~{speedup:,.0f}x faster")
print("\nNote: this compares against the LIGHTER sweep settings (30/5/1000),")
print("not the full-precision single-run baseline (120/20/4000), which would")
print("take proportionally longer. State which settings this number refers")
print("to if you cite it in the README, for accuracy.")
