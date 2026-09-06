import openmc


def build_materials(enrichment=0.045):
    """
    Builds the four materials used in the pin-cell model and exports them
    to materials.xml.

    Enrichment is the only material property that varies across sweep
    configs (control rod height and pin pitch are geometry knobs, handled
    in build_geometry.py) -- so it's the one parameter exposed here.
    Cladding, moderator, and B4C absorber compositions are fixed regardless
    of reactor parameters, matching the Day 51 plan.

    Parameters
    ----------
    enrichment : float
        U-235 weight/atom fraction in the fuel (e.g. 0.045 = 4.5%).
        U-238 fraction is set to (1.0 - enrichment) so the two always sum
        to 1.0 -- no way to accidentally leave a stale U238 fraction behind
        when enrichment changes.

    Returns
    -------
    tuple(openmc.Material, openmc.Material, openmc.Material, openmc.Material)
        (fuel, cladding, moderator, b4c), in case compile_reactor_core()
        needs direct references rather than re-importing.
    """
    if not (0.0 < enrichment < 1.0):
        raise ValueError(f"enrichment ({enrichment}) must be between 0 and 1.")

    # 1. UO2 fuel -- enrichment is the parametrized knob
    fuel = openmc.Material(name='SMR Fuel')
    fuel.set_density('g/cm3', 10.3)
    fuel.add_nuclide('U235', enrichment)
    fuel.add_nuclide('U238', 1.0 - enrichment)
    fuel.add_nuclide('O16', 2.0)

    # 2. Zircaloy-4 cladding -- fixed
    cladding = openmc.Material(name='Cladding')
    cladding.set_density('g/cm3', 6.55)
    cladding.add_element('Zr', 0.98)
    cladding.add_element('Fe', 0.02)

    # 3. Light water moderator -- fixed
    moderator = openmc.Material(name='Water Moderator')
    moderator.set_density('g/cm3', 0.74)
    moderator.add_element('H', 2.0)
    moderator.add_nuclide('O16', 1.0)
    moderator.add_s_alpha_beta('c_H_in_H2O')

    # 4. B4C control rod absorber -- fixed
    b4c = openmc.Material(name='Control Rod Absorber')
    b4c.set_density('g/cm3', 2.52)
    b4c.add_element('B', 4.0)
    b4c.add_element('C', 1.0)

    materials = openmc.Materials([fuel, cladding, moderator, b4c])
    materials.export_to_xml()

    return fuel, cladding, moderator, b4c


if __name__ == "__main__":
    # Manual sanity check: default enrichment, matching the Day 49 baseline.
    build_materials(enrichment=0.045)
    print("materials.xml successfully compiled (default enrichment=0.045).")
