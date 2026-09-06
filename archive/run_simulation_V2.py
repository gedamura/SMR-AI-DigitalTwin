"""
Orchestrates the pin-cell model end-to-end for environments (like Colab) that
don't already have OpenMC nuclear data installed:

  1. Downloads *only* the nuclides this model needs (via openmc_data_downloader),
     skipping the download if the data is already present (e.g. on Drive)
  2. Locates the resulting cross_sections.xml and points OpenMC at it
  3. Builds materials.xml (build_materials.py) and geometry.xml via
     compile_reactor_core(), then settings.xml (build_settings.py)
  4. Runs the transport calculation

Prerequisite (run once in a Colab cell before this script):
    !pip install -q openmc_data_downloader

Run with:
    python run_simulation.py
"""
import glob
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# 1. Download nuclear data BEFORE anything imports/builds openmc.Material
#    objects -- add_element()/add_nuclide() need the cross-section library
#    available at the moment they're called, not just at run time.
#
#    DATA_DIR points at Drive so the download survives Colab session
#    restarts. If cross_sections.xml already exists there, skip the network
#    call entirely instead of re-checking with the downloader every run.
# ---------------------------------------------------------------------------
DATA_DIR = "/content/drive/MyDrive/openmc_data"
os.makedirs(DATA_DIR, exist_ok=True)

matches = glob.glob(os.path.join(DATA_DIR, "**", "cross_sections.xml"), recursive=True)

if matches:
    xs_path = matches[0]
    print(f"Found existing cross section library, skipping download: {xs_path}")
else:
    print("Downloading required nuclear data (first run only, may take a minute)...")
    # Isotopes/elements/thermal-scattering laws used across build_materials.py:
    #   fuel:      U235, U238, O16
    #   cladding:  Zr, Fe (natural elements)
    #   moderator: H (natural element), O16, c_H_in_H2O S(a,b)
    #   b4c:       B, C (natural elements)
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

# ---------------------------------------------------------------------------
# 2. Now it's safe to import openmc and the build scripts. Also set
#    openmc.config directly as a belt-and-suspenders measure, since it's
#    read at call time (not just at import time).
# ---------------------------------------------------------------------------
import openmc
openmc.config['cross_sections'] = xs_path

import build_materials  # noqa: F401,E402  -> writes materials.xml (now includes b4c)
from build_geometry import compile_reactor_core  # noqa: E402

# compile_reactor_core() replaces the old "import build_geometry" side-effect
# call -- geometry.xml is now written explicitly, with a chosen rod position,
# rather than automatically on import.
CONTROL_ROD_HEIGHT = 30.0  # cm; 0.0 = fully inserted, 60.0 = fully withdrawn
compile_reactor_core(control_rod_height=CONTROL_ROD_HEIGHT)

import build_settings  # noqa: F401,E402  -> writes settings.xml

# ---------------------------------------------------------------------------
# 3. Launch the Monte Carlo k-eigenvalue calculation.
# ---------------------------------------------------------------------------
openmc.run()
