import openmc
from build_materials import build_materials


def compile_reactor_core(control_rod_height, enrichment=0.045, pin_pitch=1.26,
                          core_top=60.0):
    """
    Builds the pin-cell geometry with a movable control rod channel and
    exports it to geometry.xml.

    Day 51 change: enrichment and pin_pitch are now real inputs rather than
    hardcoded constants, so a single clean function interface can drive a
    parameter sweep (Day 52+) instead of hand-editing this file per config.

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
    enrichment : float
        U-235 enrichment fraction for the fuel, passed through to
        build_materials(). Defaults to 0.045 (4.5%), matching the Day 49
        benchmark baseline.
    pin_pitch : float
        Pin pitch (cm), i.e. the side length of the square X/Y bounding
        box around the pin cell. Defaults to 1.26 cm, the original value.
        Tighter pitch under-moderates a typical LWR lattice; wider pitch
        over-moderates it.
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
    if pin_pitch <= 0.0:
        raise ValueError(f"pin_pitch ({pin_pitch}) must be positive.")

    # Materials are rebuilt every call since enrichment can vary per config.
    # This also (re)writes materials.xml, so callers no longer need a
    # separate `import build_materials` side-effect call.
    fuel, cladding, moderator, b4c = build_materials(enrichment=enrichment)

    # Keep the rod tip strictly between the core boundaries. At exactly
    # control_rod_height=0.0 or =core_top, rod_tip would sit exactly on
    # top of core_bottom or core_top_plane -- two coincident surfaces,
    # which causes OpenMC's particle tracker to lose particles at that
    # boundary (ambiguous surface-crossing distance). The offset is
    # physically negligible but keeps the surfaces distinct.
    _epsilon = 1e-3  # cm
    control_rod_height = max(_epsilon, min(control_rod_height, core_top - _epsilon))

    # 1. Radial surfaces -- benchmark-matched dimensions from Day 49.
    #    Not parametrized: fuel/clad radii are a separate physical knob
    #    from pitch and aren't in scope for Day 51.
    fuel_outer_wall = openmc.ZCylinder(r=0.4096, name='Fuel Radius')
    clad_outer_wall = openmc.ZCylinder(r=0.4750, name='Clad Outer Radius')

    # 2. Axial surfaces. Reflective top and bottom, consistent with the
    #    reflective X/Y treatment (no axial leakage) -- a known, documented
    #    approximation.
    core_bottom = openmc.ZPlane(z0=0.0, boundary_type='reflective')
    core_top_plane = openmc.ZPlane(z0=core_top, boundary_type='reflective')

    # The rod tip itself is an internal divider, not a boundary -- particles
    # pass through it freely, it just marks where the material fill changes.
    rod_tip = openmc.ZPlane(z0=control_rod_height)

    # 3. X/Y bounding box -- now driven by pin_pitch instead of a hardcoded
    #    1.26 cm constant.
    min_x = openmc.XPlane(x0=-pin_pitch / 2, boundary_type='reflective')
    max_x = openmc.XPlane(x0=pin_pitch / 2, boundary_type='reflective')
    min_y = openmc.YPlane(y0=-pin_pitch / 2, boundary_type='reflective')
    max_y = openmc.YPlane(y0=pin_pitch / 2, boundary_type='reflective')

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
        f"geometry.xml compiled: rod tip at z={control_rod_height:.2f} cm, "
        f"enrichment={enrichment:.3f}, pitch={pin_pitch:.3f} cm "
        f"(core spans 0-{core_top:.1f} cm)"
    )
    return geometry


if __name__ == "__main__":
    # Manual sanity check when running this file directly: mid-core rod
    # position at defaults, matching the earlier Day 50 check.
    compile_reactor_core(control_rod_height=30.0)
