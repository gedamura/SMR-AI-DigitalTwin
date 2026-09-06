"""
Orchestrates the pin-cell model end-to-end for environments (like Colab) that
don't already have OpenMC nuclear data installed.

Day 51 change: the old `import build_materials` line is gone. That import
used to work because build_materials.py wrote materials.xml as a
module-level side effect on import. Now that build_materials() is a
function called from inside compile_reactor_core() (so enrichment can vary
per call), that import no longer does anything -- materials.xml gets
written automatically as part of the compile_reactor_core() call below.

Run with:
    python run_simulation.py
"""
import glob
import os
import subprocess
import sys

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
        raise RuntimeError(
            "openmc_data_downloader failed. Make sure it's installed with:\n"
            "  pip install openmc_data_downloader\n"
            "and that this Colab runtime has internet access."
        )
    matches = glob.glob(os.path.join(DATA_DIR, "**", "cross_sections.xml"), recursive=True)
    if not matches:
        raise FileNotFoundError(
            f"No cross_sections.xml found under {DATA_DIR} after download. "
            "Check the output above for download errors."
        )
    xs_path = matches[0]
    print(f"Using cross section library: {xs_path}")

os.environ["OPENMC_CROSS_SECTIONS"] = xs_path

import openmc
openmc.config['cross_sections'] = xs_path

from build_geometry import compile_reactor_core  # noqa: E402
# compile_reactor_core() now handles materials.xml internally (it calls
# build_materials() with whatever enrichment is passed in), so there's no
# separate materials import/build step here anymore.

CONTROL_ROD_HEIGHT = 30.0  # cm; 0.0 = fully inserted, 60.0 = fully withdrawn
ENRICHMENT = 0.045         # U-235 fraction; Day 49/50 baseline value
PIN_PITCH = 1.26           # cm; Day 49/50 baseline value
compile_reactor_core(
    control_rod_height=CONTROL_ROD_HEIGHT,
    enrichment=ENRICHMENT,
    pin_pitch=PIN_PITCH,
)

from build_settings import build_settings  # noqa: E402

# Explicit call required: build_settings() only runs its body when called,
# not on import (same reason compile_reactor_core() is called explicitly
# above instead of relying on an import-time side effect). The bare
# `import build_settings` used to write settings.xml as a module-level
# side effect; that logic now lives inside the function, so the old
# import-only line was silently a no-op -- settings.xml either didn't
# exist or was stale from a previous run.
build_settings()

openmc.run()
