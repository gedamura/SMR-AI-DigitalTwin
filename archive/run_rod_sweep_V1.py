"""
Runs the control rod through its two extremes (fully inserted, fully
withdrawn) to confirm control_rod_height is a working, monotonic input to
k-effective. Reuses the same materials/settings across all runs -- only
geometry.xml changes between iterations, since compile_reactor_core() is
the only piece that depends on rod position.

Run with:
    python run_rod_sweep.py
"""
import glob
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# 1. Nuclear data setup (same Drive-backed, skip-if-present logic as
#    run_simulation.py). Safe to re-run even if already configured this
#    session.
# ---------------------------------------------------------------------------
DATA_DIR = "/content/drive/MyDrive/openmc_data"
os.makedirs(DATA_DIR, exist_ok=True)

matches = glob.glob(os.path.join(DATA_DIR, "**", "cross_sections.xml"), recursive=True)

if matches:
    xs_path = matches[0]
    print(f"Found existing cross section library, skipping download: {xs_path}")
else:
    print("Downloading required nuclear data (first run only, may take a minute)...")
    download_cmd = [
        "openmc_data_downloader",
        "-l", "ENDFB-7.1-NNDC",
        "-i", "U235", "U238", "O16",
        "-e", "Zr", "Fe", "H", "B", "C",
        "-s", "c_H_in_H2O",
        "-d", DATA_DIR,
    ]
    result = subprocess.run(download_cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError("openmc_data_downloader failed -- check output above.")
    matches = glob.glob(os.path.join(DATA_DIR, "**", "cross_sections.xml"), recursive=True)
    xs_path = matches[0]

os.environ["OPENMC_CROSS_SECTIONS"] = xs_path

# ---------------------------------------------------------------------------
# 2. Build materials and settings once -- these don't depend on rod height.
# ---------------------------------------------------------------------------
import openmc
openmc.config['cross_sections'] = xs_path

import build_materials  # noqa: F401,E402  -> writes materials.xml
from build_geometry import compile_reactor_core  # noqa: E402
import build_settings  # noqa: F401,E402  -> writes settings.xml (fuel-distributed source)

# ---------------------------------------------------------------------------
# 3. Run the two extremes. (Mid-core h=30 was already run separately --
#    add it here too if you want all three in one summary table.)
# ---------------------------------------------------------------------------
rod_heights = [0.0, 60.0]
results = []

for h in rod_heights:
    label = "fully inserted" if h == 0.0 else "fully withdrawn" if h == 60.0 else "partial"
    print(f"\n--- Running control_rod_height = {h:.1f} cm ({label}) ---")

    compile_reactor_core(control_rod_height=h)
    openmc.run(output=False)

    sp_files = sorted(glob.glob("statepoint.*.h5"))
    sp = openmc.StatePoint(sp_files[-1])
    keff_mean = sp.keff.n
    keff_std = sp.keff.s
    sp.close()

    results.append((h, label, keff_mean, keff_std))
    print(f"control_rod_height={h:.1f} cm -> k-effective = {keff_mean:.5f} +/- {keff_std:.5f}")

# ---------------------------------------------------------------------------
# 4. Summary table
# ---------------------------------------------------------------------------
print("\n=== Control rod sweep summary ===")
for h, label, k, s in results:
    print(f"h={h:5.1f} cm ({label:16s}) | k-eff = {k:.5f} +/- {s:.5f}")
