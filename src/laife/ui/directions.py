"""Coordinates and directions."""

from enum import Enum
import math

from laife.config.types import Position


class CardinalDirection(Enum):
    North = "north"
    South = "south"
    East = "east"
    West = "west"
    NorthEast = "northeast"
    NorthWest = "northwest"
    SouthEast = "southeast"
    SouthWest = "southwest"


def pospos2cardinal_direction(you: Position, target: Position) -> CardinalDirection:
    """Convert two positions to cardinal coordinates.

    The cardinal coordinates are based on the direction from you to the target.
    """
    cardinal_degrees = pospos2cardinal_degrees(you, target)
    if 0 * 45 + 22.5 <= cardinal_degrees < 1 * 45 + 22.5:
        return CardinalDirection.NorthEast
    elif 1 * 45 + 22.5 <= cardinal_degrees < 2 * 45 + 22.5:
        return CardinalDirection.East
    elif 2 * 45 + 22.5 <= cardinal_degrees < 3 * 45 + 22.5:
        return CardinalDirection.SouthEast
    elif 3 * 45 + 22.5 <= cardinal_degrees < 4 * 45 + 22.5:
        return CardinalDirection.South
    elif 4 * 45 + 22.5 <= cardinal_degrees < 5 * 45 + 22.5:
        return CardinalDirection.SouthWest
    elif 5 * 45 + 22.5 <= cardinal_degrees < 6 * 45 + 22.5:
        return CardinalDirection.West
    elif 6 * 45 + 22.5 <= cardinal_degrees < 7 * 45 + 22.5:
        return CardinalDirection.NorthWest
    else:
        return CardinalDirection.North


def pospos2cardinal_degrees(you: Position, target: Position) -> float:
    """Convert two positions to cardinal coordinates.

    Note that in pygame, the y-axis is flipped.
    """
    dx = target[0] - you[0]
    dy = -(target[1] - you[1])
    if dx == 0 and dy == 0:
        return 0
    polar_radians = math.atan2(dy, dx)
    polar_degrees = math.degrees(polar_radians)
    cardinal_degrees = (90 - polar_degrees) % 360
    return cardinal_degrees
