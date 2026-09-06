"""
Day 52: defines the bounded parameter grid that Day 53's execution loop
iterates over.

Refactored as a function (build_sweep_grid()) rather than module-level
code, same pattern as build_materials()/build_settings(), so run_sweep.py
can import it directly instead of duplicating the grid definition.
"""
import itertools
import numpy as np

CORE_TOP = 60.0  # cm; must match compile_reactor_core()'s default core_top


def build_sweep_grid(n_rod_positions=10,
                      enrichments=(0.03, 0.045, 0.07),
                      pitches=(1.10, 1.26, 1.42),
                      core_top=CORE_TOP):
    """
    Builds the bounded (rod_height, enrichment, pitch) parameter grid.

    Centered on the Day 49/50 baseline (enrichment=0.045, pin_pitch=1.26)
    and bracketed by the exact extremes already sanity-checked in Day 51
    (enrichment=0.07, pin_pitch=1.10) -- so the sweep explores parameter
    space already known to behave physically, not an untested region.

    Returns
    -------
    list of tuple(float, float, float)
        (rod_height, enrichment, pitch) for each config.
    """
    rod_heights = np.linspace(0.0, core_top, n_rod_positions)
    sweep_grid = list(itertools.product(rod_heights, enrichments, pitches))
    return sweep_grid


if __name__ == "__main__":
    grid = build_sweep_grid()
    print(f"Sweep grid built: {len(grid)} configurations queued.")
    print("\nFirst 5 configs:")
    for height, enrichment, pitch in grid[:5]:
        print(f"  height={height:.2f} cm, enrichment={enrichment}, pitch={pitch}")
    print("\nLast 5 configs:")
    for height, enrichment, pitch in grid[-5:]:
        print(f"  height={height:.2f} cm, enrichment={enrichment}, pitch={pitch}")
