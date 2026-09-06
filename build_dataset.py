"""
Day 55/56: scrapes the real k-effective value out of each statepoint
produced by run_sweep.py, and assembles them into a CSV alongside their
(rod_height, enrichment, pitch) config.

No simulation runs here -- this reads statepoint_run<index>.h5 files
already on disk from Day 53's sweep. Matches the plan's fault-tolerant
philosophy: rows with a missing/unreadable statepoint are logged and
dropped, never replaced with a fabricated number. No np.random.normal
anywhere in this file.

Run with:
    python build_dataset.py
"""
import glob
import os

import pandas as pd
import openmc

from build_sweep_grid import build_sweep_grid

CORE_TOP = 60.0


def scrape_criticality_value(index):
    """
    Opens statepoint_run<index>.h5 and returns k-eff (mean, std), or
    (None, None) if the file is missing or unreadable.
    """
    statepoint_file = f"statepoint_run{index}.h5"
    try:
        sp = openmc.StatePoint(statepoint_file)
        keff_mean = sp.keff.n
        keff_std = sp.keff.s
        sp.close()
        return keff_mean, keff_std
    except (FileNotFoundError, OSError) as e:
        print(f"  Could not read {statepoint_file}: {e}")
        return None, None


sweep_grid = build_sweep_grid(core_top=CORE_TOP)
print(f"Scraping {len(sweep_grid)} configs from disk...\n")

records = []
failures = []

for index, (height, enrichment, pitch) in enumerate(sweep_grid):
    keff_mean, keff_std = scrape_criticality_value(index)

    if keff_mean is None:
        failures.append(index)
        with open("pipeline_failures.log", "a") as log:
            log.write(
                f"Run #{index} (h={height:.2f}, e={enrichment}, p={pitch}): "
                f"statepoint_run{index}.h5 missing or unreadable\n"
            )
        continue

    records.append({
        "run_index": index,
        "control_rod_height_cm": height,
        "enrichment": enrichment,
        "pin_pitch_cm": pitch,
        "k_effective_mean": keff_mean,
        "k_effective_std": keff_std,
    })

smr_dataset = pd.DataFrame(records)
smr_dataset.to_csv("smr_neutronics_dataset.csv", index=False)

print(f"Dataset built from {len(records)}/{len(sweep_grid)} successful real simulations.")
if failures:
    print(f"{len(failures)} run(s) failed to scrape (indices: {failures}) -- see pipeline_failures.log")
else:
    print("No missing/unreadable statepoints -- all 90 rows are real.")

print(f"\nSaved: smr_neutronics_dataset.csv ({len(records)} rows)")
print(smr_dataset.head())
