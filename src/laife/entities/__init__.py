"""Entities package — public API."""

from laife.entities.building_data import BuildingData
from laife.entities.building_sprite import BuildingSprite
from laife.entities.geometry import aabb_collides
from laife.entities.player_agent import PlayerAgent
from laife.entities.player_sprite import PlayerSprite
from laife.entities.player_state import PlayerState
from laife.entities.world_renderer import WorldRenderer
from laife.entities.world_runner import WorldRunner

__all__ = [  # noqa: RUF022
    # data / logic
    "BuildingData",
    "PlayerAgent",
    "PlayerState",
    "WorldRunner",
    # rendering
    "BuildingSprite",
    "PlayerSprite",
    "WorldRenderer",
    # utilities
    "aabb_collides",
]
