import openmc
from build_materials import fuel, cladding, moderator

# 1. Define infinite geometric cylinder surfaces along the Z-axis
fuel_outer_wall = openmc.ZCylinder(r=0.39, name='Fuel Radius')
clad_outer_wall = openmc.ZCylinder(r=0.45, name='Clad Outer Radius')

# 2. Slice space into bounded volumetric cells using intersections and signs
fuel_cell = openmc.Cell(name='Fuel Region', fill=fuel, region=-fuel_outer_wall)
clad_cell = openmc.Cell(name='Clad Region', fill=cladding, region=+fuel_outer_wall & -clad_outer_wall)
mod_cell = openmc.Cell(name='Moderator Region', fill=moderator, region=+clad_outer_wall)

# 3. Define an infinite bounding box lattice along the X and Y dimensions (pitch = 1.26 cm)
pitch = 1.26
min_x = openmc.XPlane(x0=-pitch/2, boundary_type='reflective')
max_x = openmc.XPlane(x0=pitch/2, boundary_type='reflective')
min_y = openmc.YPlane(y0=-pitch/2, boundary_type='reflective')
max_y = openmc.YPlane(y0=pitch/2, boundary_type='reflective')

# 4. Enforce the bounding box limits onto the outermost moderator region
mod_cell.region = mod_cell.region & +min_x & -max_x & +min_y & -max_y

# 5. Pack cells into a primary operational universe container and export to XML
root_universe = openmc.Universe(cells=[fuel_cell, clad_cell, mod_cell])
geometry = openmc.Geometry(root_universe)
geometry.export_to_xml()
print("geometry.xml successfully compiled with reflective boundary conditions.")
