"""
Day 53: loops over the Day 52 parameter grid, calling compile_reactor_core()
and running OpenMC for every (rod_height, enrichment, pitch) config. Each
run produces a real statepoint.<index>.h5 tied to that config's position in
the grid.

Uses the lighter settings (batches=30, inactive=5, particles=1000)
validated in the Day 51 fast re-check -- necessary for 90 runs to finish
in a reasonable time, at the cost of larger per-point k-eff uncertainty.
openmc.run(output=False) is already used here to keep terminal output
manageable across 90 runs (this folds in what the plan calls out
separately as Day 54).

This step does NOT yet include fault tolerance (Day 55/56) -- if any run
in the loop raises, the whole script stops. That's deliberate for now:
better to see the first failure clearly than to silently skip it.

IMPORTANT NAMING NOTE: OpenMC names statepoint files after the batch
number (e.g. statepoint.30.h5 since batches=30), not the sweep loop index.
Left alone, every run in this loop would overwrite the same file. This
script renames each statepoint immediately after it's produced, to
statepoint_run<index>.h5, so all 90 survive and can be matched back to
their (height, enrichment, pitch) config later.

Run with:
    python run_sweep.py
"""
import glob
import os
import shutil

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
from build_sweep_grid import build_sweep_grid  # noqa: E402

CORE_TOP = 60.0

# Settings don't depend on rod height/enrichment/pitch -- build once,
# reused across all 90 runs. Lighter settings for sweep speed.
build_settings(batches=30, inactive=5, particles=1000, core_top=CORE_TOP)

sweep_grid = build_sweep_grid(core_top=CORE_TOP)
print(f"Sweep grid built: {len(sweep_grid)} configurations queued.\n")

for index, (height, enrichment, pitch) in enumerate(sweep_grid):
    print(f"--- Run [#{index}/{len(sweep_grid) - 1}] "
          f"height={height:.2f} enr={enrichment} pitch={pitch} ---")
    compile_reactor_core(
        control_rod_height=height,
        enrichment=enrichment,
        pin_pitch=pitch,
        core_top=CORE_TOP,
    )
    openmc.run(output=False)

    # OpenMC always names the output after the batch count (statepoint.30.h5
    # here, regardless of which sweep config produced it) -- rename it now,
    # before the next iteration's run overwrites it.
    raw_statepoint = glob.glob("statepoint.*.h5")
    if len(raw_statepoint) != 1:
        raise RuntimeError(
            f"Run [#{index}] expected exactly one statepoint.*.h5 file, "
            f"found {raw_statepoint}. Check for leftover files from a "
            f"previous session before continuing."
        )
    indexed_name = f"statepoint_run{index}.h5"
    shutil.move(raw_statepoint[0], indexed_name)

print(f"\nDone: {len(sweep_grid)} statepoint files written "
      f"(statepoint_run0.h5 through statepoint_run{len(sweep_grid) - 1}.h5).")
