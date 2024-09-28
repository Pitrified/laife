"""Test the directions module."""

import pytest

from laife.config.types import Position
from laife.ui.directions import CardinalDirection, pospos2cardinal_direction


@pytest.mark.parametrize(
    "you, target, expected_direction",
    [
        ((0, 0), (0, -1), CardinalDirection.North),
        ((0, 0), (1, -1), CardinalDirection.NorthEast),
        ((0, 0), (1, 0), CardinalDirection.East),
        ((0, 0), (1, 1), CardinalDirection.SouthEast),
        ((0, 0), (0, 1), CardinalDirection.South),
        ((0, 0), (-1, 1), CardinalDirection.SouthWest),
        ((0, 0), (-1, 0), CardinalDirection.West),
        ((0, 0), (-1, -1), CardinalDirection.NorthWest),
    ],
)
def test_pospos2cardinal_direction(
    you: Position,
    target: Position,
    expected_direction: CardinalDirection,
) -> None:
    """Test that pospos2cardinal_direction works."""
    assert pospos2cardinal_direction(you, target) == expected_direction


def test_pospos2cardinal_direction_same():
    """Test that pospos2cardinal_direction works when the positions are the same."""
    you = (0, 0)
    target = (0, 0)
    expected_direction = CardinalDirection.North
    assert pospos2cardinal_direction(you, target) == expected_direction
