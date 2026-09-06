import openmc

settings = openmc.Settings()

# 1. Define spatial coordinates for the point source distribution directly in the fuel center
source_point = openmc.stats.Point(xyz=(0.0, 0.0, 0.0))
# Fix: openmc.Source is deprecated in current OpenMC releases (installed via
# conda-forge on Colab) and raises a DeprecationWarning / breaks on some
# versions. IndependentSource is the current class for this.
settings.source = openmc.IndependentSource(space=source_point)

# 2. Explicitly set the run mode (k-eigenvalue criticality calculation)
settings.run_mode = 'eigenvalue'

# 3. Configure computational overhead constraints
settings.batches = 120          # Total execution cycles
settings.inactive = 20          # Startup batches discarded from statistics
settings.particles = 4000       # Neutron histories tracked concurrently per batch

settings.export_to_xml()
print("settings.xml execution profiles successfully compiled.")
