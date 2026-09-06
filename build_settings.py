import openmc


def build_settings(batches=120, inactive=20, particles=4000, core_top=60.0):
    """
    Builds the fuel-distributed source and run parameters, exports to
    settings.xml.

    Defaults (120/20/4000) match the Day 49/50 validated baseline. For
    sweep runs where speed matters more than per-point precision, pass
    lighter values, e.g. build_settings(batches=30, inactive=5,
    particles=1000) -- matches the Day 53 plan's suggested sweep settings.
    Reduced particle count trades statistical precision for speed: fewer
    active histories means larger k-eff uncertainty (sigma scales roughly
    as 1/sqrt(N)), and fewer inactive batches risks an under-converged
    fission source going into the active batches, which biases k-eff
    rather than just adding noise. Worth spot-checking Shannon entropy
    convergence on a couple of sweep configs if this matters later.

    Parameters
    ----------
    batches : int
        Total execution cycles.
    inactive : int
        Startup batches discarded from statistics (source convergence).
    particles : int
        Neutron histories tracked per batch.
    core_top : float
        Must match compile_reactor_core()'s core_top -- used to keep the
        source box inset from the axial boundaries.

    Returns
    -------
    openmc.Settings
    """
    fuel_radius = 0.4096  # cm, must match build_geometry.py's fuel_outer_wall

    # Box drawn well inside the fuel radius, pulled in 2 cm from the core
    # top/bottom so it can't land on either axial boundary.
    box_half_width = fuel_radius * 0.6
    source_box = openmc.stats.Box(
        lower_left=(-box_half_width, -box_half_width, 2.0),
        upper_right=(box_half_width, box_half_width, core_top - 2.0),
        only_fissionable=True,
    )

    settings = openmc.Settings()
    settings.source = openmc.Source(space=source_box)
    settings.batches = batches
    settings.inactive = inactive
    settings.particles = particles
    settings.export_to_xml()

    print(
        f"settings.xml compiled: batches={batches}, inactive={inactive}, "
        f"particles={particles} ({(batches - inactive) * particles} active histories)"
    )
    return settings


if __name__ == "__main__":
    # Manual sanity check: Day 49/50 validated baseline settings.
    build_settings()
