"""Coordinates and directions."""

from enum import Enum
import math

from laife.config.types import Position


class Cardinal(Enum):
    North = "north"
    South = "south"
    East = "east"
    West = "west"
    NorthEast = "northeast"
    NorthWest = "northwest"
    SouthEast = "southeast"
    SouthWest = "southwest"


def pospos2cardinal(you: Position, target: Position) -> Cardinal:
    """Convert two positions to cardinal coordinates.

    The cardinal coordinates are based on the direction from you to the target.
    """
    card_float = pospos2cardinal_float(you, target)
    if 0 * 45 + 22.5 <= card_float < 1 * 45 + 22.5:
        return Cardinal.NorthEast
    elif 1 * 45 + 22.5 <= card_float < 2 * 45 + 22.5:
        return Cardinal.East
    elif 2 * 45 + 22.5 <= card_float < 3 * 45 + 22.5:
        return Cardinal.SouthEast
    elif 3 * 45 + 22.5 <= card_float < 4 * 45 + 22.5:
        return Cardinal.South
    elif 4 * 45 + 22.5 <= card_float < 5 * 45 + 22.5:
        return Cardinal.SouthWest
    elif 5 * 45 + 22.5 <= card_float < 6 * 45 + 22.5:
        return Cardinal.West
    elif 6 * 45 + 22.5 <= card_float < 7 * 45 + 22.5:
        return Cardinal.NorthWest
    else:
        return Cardinal.North


def pospos2cardinal_float(you: Position, target: Position) -> float:
    """Convert two positions to cardinal coordinates."""
    dx = target[0] - you[0]
    dy = target[1] - you[1]
    if dx == 0 and dy == 0:
        return 0
    radians = math.atan2(dy, dx)
    deg = math.degrees(radians)
    card_float = (90 - deg + 360) % 360
    return card_float
