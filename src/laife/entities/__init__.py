"""Entities package - public API.

The simulation only: nothing here draws or serves; the world page reads it
through ``laife.web``.
"""

from llm_core.vectorstores.vectorable import Vectorable

from laife.entities.building import Building
from laife.entities.building import BuildingType
from laife.entities.building_types import BUILDING_TYPES
from laife.entities.player import Player
from laife.entities.player import PlayerState
from laife.entities.utensil import Utensil
from laife.entities.utils.geometry import aabb_collides
from laife.entities.world_runner import WorldRunner

__all__ = [  # noqa: RUF022
    # data / logic
    "Building",
    "BuildingType",
    "BUILDING_TYPES",
    "Player",
    "PlayerState",
    "Utensil",
    "Vectorable",
    "WorldRunner",
    # utilities
    "aabb_collides",
]
