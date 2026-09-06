"""
Same Day 51 sanity check as before (default vs. high enrichment vs. tight
pitch, rod fully withdrawn), but using lighter settings for speed:
batches=30, inactive=5, particles=1000 instead of the Day 49/50 baseline
120/20/4000.

Tradeoff: statistical uncertainty (sigma) on each k-eff will be roughly
4x larger than the original run. That's still fine for THIS check, since
the Day 51 effects were huge (~29 sigma and ~65 sigma at full precision) --
a 4x noisier sigma still leaves both comparisons far from borderline.
It would NOT necessarily be fine for comparisons with smaller expected
deltas (e.g. adjacent rod-height points in Day 52's grid), so don't
assume this settings choice generalizes without checking magnitude vs.
sigma again for those cases.

Run with:
    python validate_day51_sanity_fast.py
"""
import glob
import os

DATA_DIR = "/content/drive/MyDrive/openmc_data"
matches = glob.glob(os.path.join(DATA_DIR, "**", "cross_sections.xml"), recursive=True)
if not matches:
    raise FileNotFoundError(
        f"No cross_sections.xml found under {DATA_DIR}. Run run_simulation.py "
        "once first so the nuclear data download step completes."
    )
os.environ["OPENMC_CROSS_SECTIONS"] = matches[0]

import openmc  # noqa: E402
openmc.config['cross_sections'] = matches[0]

from build_geometry import compile_reactor_core  # noqa: E402
from build_settings import build_settings  # noqa: E402

CORE_TOP = 60.0

# Lighter settings, built once and reused across all three runs -- same as
# before, settings don't depend on rod height/enrichment/pitch.
build_settings(batches=30, inactive=5, particles=1000, core_top=CORE_TOP)

configs = [
    ("default",        dict(enrichment=0.045, pin_pitch=1.26)),
    ("high enrichment", dict(enrichment=0.07,  pin_pitch=1.26)),
    ("tight pitch",     dict(enrichment=0.045, pin_pitch=1.10)),
]

results = []
for label, params in configs:
    print(f"\n--- Running {label}: {params} ---")
    compile_reactor_core(control_rod_height=CORE_TOP, core_top=CORE_TOP, **params)
    openmc.run(output=False)

    sp_files = sorted(glob.glob("statepoint.*.h5"))
    sp = openmc.StatePoint(sp_files[-1])
    keff_mean, keff_std = sp.keff.n, sp.keff.s
    sp.close()

    results.append((label, params, keff_mean, keff_std))
    print(f"{label} -> k-eff = {keff_mean:.5f} +/- {keff_std:.5f}")

print("\n=== Day 51 sanity check summary (lighter settings) ===")
for label, params, k, s in results:
    print(f"{label:16s} {params} | k-eff = {k:.5f} +/- {s:.5f}")

base_k = results[0][2]
high_enr_k = results[1][2]
tight_pitch_k = results[2][2]

print("\nDirection checks:")
print(f"  High enrichment vs default: {'PASS (k-eff rose)' if high_enr_k > base_k else 'FAIL (expected k-eff to rise)'}")
print(f"  Tight pitch vs default:     {'PASS (k-eff fell)' if tight_pitch_k < base_k else 'FAIL (expected k-eff to fall)'}")
