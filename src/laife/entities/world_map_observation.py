"""Structured spatial observation of the world around a player."""

from __future__ import annotations

import math

from pydantic import BaseModel

from laife.config.types import Position  # noqa: TC001
from laife.entities.utils.directions import pospos2cardinal_direction

_ORIGIN: Position = (0, 0)


class NearbyEntity(BaseModel):
    """A single entity visible to the observing player."""

    entity_type: str  # "building" | "player"
    name: str
    relative_position: tuple[int, int]  # (dx, dy) from the observing player
    distance: float


class WorldMapObservation(BaseModel):
    """Structured spatial snapshot of the world centred on a player."""

    player_position: Position
    nearby_entities: list[NearbyEntity]
    radius: int = 20

    @staticmethod
    def from_position(position: Position) -> WorldMapObservation:
        """Return an empty observation centred on *position*."""
        return WorldMapObservation(player_position=position, nearby_entities=[])

    def to_prompt(self) -> str:
        """Return a human-readable text description for the LLM."""
        lines: list[str] = [f"You are at position {self.player_position}."]

        if not self.nearby_entities:
            lines.append("Nothing is nearby.")
            return "\n".join(lines)

        lines.append(f"Nearby entities (within {self.radius} tiles):")
        for entity in self.nearby_entities:
            direction = pospos2cardinal_direction(_ORIGIN, entity.relative_position)
            lines.append(
                f'- {entity.entity_type.capitalize()} "{entity.name}"'
                f" is to the {direction.value} (distance {entity.distance:.1f})."
            )
        return "\n".join(lines)


def euclidean(a: Position, b: Position) -> float:
    """Return the Euclidean distance between two positions."""
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return math.sqrt(dx * dx + dy * dy)
