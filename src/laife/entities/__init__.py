"""Entities package - public API."""

from laife.entities.building import Building
from laife.entities.player import Player
from laife.entities.player import PlayerState
from laife.entities.utils.geometry import aabb_collides
from laife.entities.world_runner import WorldRunner
from laife.rendering.building_sprite import BuildingSprite
from laife.rendering.player_sprite import PlayerSprite
from laife.rendering.world_renderer import WorldRenderer

__all__ = [  # noqa: RUF022
    # data / logic
    "Building",
    "Player",
    "PlayerState",
    "WorldRunner",
    # rendering
    "BuildingSprite",
    "PlayerSprite",
    "WorldRenderer",
    # utilities
    "aabb_collides",
]
