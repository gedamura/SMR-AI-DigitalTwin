import openmc
from build_materials import fuel, cladding, moderator, b4c


def compile_reactor_core(control_rod_height, core_top=60.0):
    """
    Builds the pin-cell geometry with a movable control rod channel and
    exports it to geometry.xml.

    The fuel and cladding are present across the full active core height,
    unchanged by rod position -- physically, the fuel pin itself is never
    replaced. What actually moves is the material filling the channel
    outside the clad: moderator below the rod tip, B4C absorber above it.

    Parameters
    ----------
    control_rod_height : float
        Z-coordinate (cm) of the rod tip, measured from the bottom of the
        active core (z=0). 0.0 = fully inserted (B4C fills the whole
        channel). core_top = fully withdrawn (moderator fills the whole
        channel).
    core_top : float
        Height of the active core in cm. Defaults to 60.0 cm to match the
        Week 8 parameter sweep range.

    Returns
    -------
    openmc.Geometry
        The compiled geometry object (also exported to geometry.xml).
    """
    if not (0.0 <= control_rod_height <= core_top):
        raise ValueError(
            f"control_rod_height ({control_rod_height}) must be between "
            f"0.0 and core_top ({core_top})."
        )

    # Keep the rod tip strictly between the core boundaries. At exactly
    # control_rod_height=0.0 or =core_top, rod_tip would sit exactly on
    # top of core_bottom or core_top_plane -- two coincident surfaces,
    # which causes OpenMC's particle tracker to lose particles at that
    # boundary (ambiguous surface-crossing distance). The offset is
    # physically negligible but keeps the surfaces distinct.
    _epsilon = 1e-3  # cm
    control_rod_height = max(_epsilon, min(control_rod_height, core_top - _epsilon))

    # 1. Radial surfaces -- benchmark-matched dimensions from Day 49
    fuel_outer_wall = openmc.ZCylinder(r=0.4096, name='Fuel Radius')
    clad_outer_wall = openmc.ZCylinder(r=0.4750, name='Clad Outer Radius')

    # 2. Axial surfaces. The model was previously infinite in Z; a movable
    #    rod requires real core bounds for the first time. Reflective top
    #    and bottom keep this consistent with the reflective X/Y treatment
    #    already in use -- same simplification (no axial leakage), applied
    #    to the new dimension. Worth a one-line README note as a known
    #    approximation.
    core_bottom = openmc.ZPlane(z0=0.0, boundary_type='reflective')
    core_top_plane = openmc.ZPlane(z0=core_top, boundary_type='reflective')

    # The rod tip itself is an internal divider, not a boundary -- particles
    # pass through it freely, it just marks where the material fill changes.
    rod_tip = openmc.ZPlane(z0=control_rod_height)

    # 3. X/Y bounding box (unchanged from the original pin-cell lattice)
    pitch = 1.26
    min_x = openmc.XPlane(x0=-pitch / 2, boundary_type='reflective')
    max_x = openmc.XPlane(x0=pitch / 2, boundary_type='reflective')
    min_y = openmc.YPlane(y0=-pitch / 2, boundary_type='reflective')
    max_y = openmc.YPlane(y0=pitch / 2, boundary_type='reflective')

    axial_bounds = +core_bottom & -core_top_plane
    xy_bounds = +min_x & -max_x & +min_y & -max_y

    # 4. Fuel and clad: constant across the full core height
    fuel_cell = openmc.Cell(
        name='Fuel Region',
        fill=fuel,
        region=-fuel_outer_wall & axial_bounds,
    )
    clad_cell = openmc.Cell(
        name='Clad Region',
        fill=cladding,
        region=+fuel_outer_wall & -clad_outer_wall & axial_bounds,
    )

    # 5. Rod channel: the region outside the clad, split at the rod tip.
    #    This is the one real physics knob -- sweeping control_rod_height
    #    moves the B4C/moderator boundary and actually changes k-effective.
    channel_xy = +clad_outer_wall & xy_bounds

    withdrawn_cell = openmc.Cell(
        name='Rod Channel - Moderator (withdrawn)',
        fill=moderator,
        region=channel_xy & +core_bottom & -rod_tip,
    )
    inserted_cell = openmc.Cell(
        name='Rod Channel - B4C (inserted)',
        fill=b4c,
        region=channel_xy & +rod_tip & -core_top_plane,
    )

    # 6. Assemble and export
    root_universe = openmc.Universe(
        cells=[fuel_cell, clad_cell, withdrawn_cell, inserted_cell]
    )
    geometry = openmc.Geometry(root_universe)
    geometry.export_to_xml()

    print(
        f"geometry.xml compiled: rod tip at z={control_rod_height:.2f} cm "
        f"(core spans 0-{core_top:.1f} cm)"
    )
    return geometry


if __name__ == "__main__":
    # Manual sanity check when running this file directly: mid-core rod
    # position, matching the "h = 30 cm" panel from the earlier diagram.
    compile_reactor_core(control_rod_height=30.0)
