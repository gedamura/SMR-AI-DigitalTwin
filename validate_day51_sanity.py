"""
Day 51 regression check: confirms enrichment and pin_pitch are wired
correctly into compile_reactor_core() by checking k-effective moves in the
physically expected direction for each.

  - Default:        enrichment=0.045, pitch=1.26  (Day 49/50 baseline)
  - High enrichment: enrichment=0.07, pitch=1.26  -> k-eff should INCREASE
  - Tight pitch:      enrichment=0.045, pitch=1.10 -> k-eff should DECREASE
                       (under-moderates a typical LWR lattice)

Rod is held fully withdrawn (control_rod_height=core_top) in all three runs
so the comparison isolates enrichment/pitch effects from rod position.

Run with:
    python validate_day51_sanity.py
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
import build_settings  # noqa: F401,E402  -> writes settings.xml once, reused across runs

CORE_TOP = 60.0

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

print("\n=== Day 51 sanity check summary ===")
for label, params, k, s in results:
    print(f"{label:16s} {params} | k-eff = {k:.5f} +/- {s:.5f}")

base_k = results[0][2]
high_enr_k = results[1][2]
tight_pitch_k = results[2][2]

print("\nDirection checks:")
print(f"  High enrichment vs default: {'PASS (k-eff rose)' if high_enr_k > base_k else 'FAIL (expected k-eff to rise)'}")
print(f"  Tight pitch vs default:     {'PASS (k-eff fell)' if tight_pitch_k < base_k else 'FAIL (expected k-eff to fall)'}")
