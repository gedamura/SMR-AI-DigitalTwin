import openmc

settings = openmc.Settings()

# Source distributed across a small region inside the fuel pin, rather than
# a single fixed point. The previous point source at (0.0, 0.0, 0.0) sat
# exactly on the core-bottom boundary plane introduced in Day 50's axial
# bounds -- that's what caused "could not find cell" / lost-particle errors.
# A fixed point is also fragile going forward: at any future rod height
# where control_rod_height lands on the same z as the source, the same
# problem recurs on the internal rod-tip divider. Sampling over a small
# volume avoids landing exactly on any surface, boundary or internal.
fuel_radius = 0.4096   # cm, must match build_geometry.py's fuel_outer_wall
core_top = 60.0        # cm, must match compile_reactor_core()'s default core_top

# Box drawn well inside the fuel radius (corner-to-center distance stays
# under fuel_radius even at the box corners) and pulled in 2 cm from the
# core top/bottom so it can't land on either axial boundary.
box_half_width = fuel_radius * 0.6
source_box = openmc.stats.Box(
    lower_left=(-box_half_width, -box_half_width, 2.0),
    upper_right=(box_half_width, box_half_width, core_top - 2.0),
    only_fissionable=True,  # rejects any sampled point that isn't in fuel
)
settings.source = openmc.Source(space=source_box)

# 2. Configure computational overhead constraints
settings.batches = 120          # Total execution cycles
settings.inactive = 20          # Startup batches discarded from statistics
settings.particles = 4000       # Neutron histories tracked concurrently per batch

settings.export_to_xml()
print("settings.xml execution profiles successfully compiled.")
