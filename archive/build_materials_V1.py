import openmc

# 1. Instantiate the Uranium Dioxide (UO2) fuel mixture enriched to 4.5% U-235
fuel = openmc.Material(name='SMR Fuel')
fuel.set_density('g/cm3', 10.3)
fuel.add_nuclide('U235', 0.045)
fuel.add_nuclide('U238', 0.955)
fuel.add_nuclide('O16', 2.0)  # Replaced natural element 'O' with explicit O16

# 2. Instantiate Zircaloy-4 for structural fuel cladding tubes
cladding = openmc.Material(name='Cladding')
cladding.set_density('g/cm3', 6.55)
cladding.add_element('Zr', 0.98)
cladding.add_element('Fe', 0.02)

# 3. Instantiate Light Water moderator containing thermal scattering laws
moderator = openmc.Material(name='Water Moderator')
moderator.set_density('g/cm3', 0.74) # Density at operating temperature/pressure
moderator.add_element('H', 2.0)
moderator.add_nuclide('O16', 1.0)  # Replaced natural element 'O' with explicit O16
moderator.add_s_alpha_beta('c_H_in_H2O') # Adds molecular binding thermal treatment

# 4. Compile and export materials array to a standardized XML configuration
materials = openmc.Materials([fuel, cladding, moderator])
materials.export_to_xml()
print("materials.xml successfully compiled.")
