"""Starting set of Terrain instances seeded into a new world.

These constants serve two purposes:

1. Seed the starting world (placed during world initialisation).
2. Pre-populate the vector DB for semantic look-ups, e.g. a player asking
   about "a place to chop wood" can be matched to ``NORTHERN_FOREST``.
"""

from laife.entities.terrain import Terrain
from laife.entities.terrain import TerrainType

NORTHERN_FOREST = Terrain(
    name="Northern Forest",
    terrain_type=TerrainType.FOREST,
    position=(0, 0),
    size=(200, 300),
    description="A dense woodland full of tall oaks.",
)

CRYSTAL_LAKE = Terrain(
    name="Crystal Lake",
    terrain_type=TerrainType.LAKE,
    position=(600, 100),
    size=(200, 150),
    description="A clear freshwater lake.",
)

RIVER_FIELDS = Terrain(
    name="River Fields",
    terrain_type=TerrainType.FERTILE_LAND,
    position=(250, 400),
    size=(300, 200),
    description="Rich soil fed by nearby streams.",
)

OPEN_PLAIN = Terrain(
    name="Open Plain",
    terrain_type=TerrainType.PLAIN,
    position=(0, 600),
    size=(900, 200),
    description="Flat open grassland good for traversal.",
)

# Ordered list - used to seed a new world.
TERRAINS: list[Terrain] = [NORTHERN_FOREST, CRYSTAL_LAKE, RIVER_FIELDS, OPEN_PLAIN]
