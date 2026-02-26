"""Starting set of BuildingType instances.

These constants represent the initial catalogue of building types available
when a new world is created.  They serve two purposes:

1. Seed the starting world (placed during world initialisation).
2. Pre-populate the vector DB (feature 16) so the world can do semantic
   look-ups, e.g. a player asking to build a "shelter" can be matched to
   ``HOUSE``.

New types discovered or invented by players during a run will be added to
the vector DB dynamically and are not listed here.
"""

from laife.entities.building import BuildingType

HOUSE = BuildingType(
    building_type="house",
    description="A place to rest safely.",
    size=(64, 64),
)

FARM = BuildingType(
    building_type="farm",
    description="A place to grow food.",
    size=(96, 64),
)

FACTORY = BuildingType(
    building_type="factory",
    description="A place to make things.",
    size=(128, 96),
)

# Ordered list - also used to iterate over the full starting catalogue.
BUILDING_TYPES: list[BuildingType] = [HOUSE, FARM, FACTORY]
