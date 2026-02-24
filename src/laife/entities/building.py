"""Building entity module — re-exports for backward compatibility.

New code should import directly from:
  laife.entities.building_data  (BuildingData)
  laife.entities.building_sprite (BuildingSprite)
"""

from laife.entities.building_data import BUILDING_DESCRIPTIONS
from laife.entities.building_data import BUILDING_TYPES
from laife.entities.building_data import BuildingData
from laife.entities.building_sprite import BuildingSprite

# Alias so that ``from laife.entities.building import Building`` keeps working.
Building = BuildingData

__all__ = [
    "BUILDING_DESCRIPTIONS",
    "BUILDING_TYPES",
    "Building",
    "BuildingData",
    "BuildingSprite",
]

# ---- original implementation has moved to building_data.py / building_sprite.py ----
