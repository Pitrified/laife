"""Test the directions module."""

import pytest

from laife.ui.directions import CardinalDirection, pospos2cardinal_direction


def test_pospos2cardinal_direction():
    """Test that pospos2cardinal_direction works."""
    you = (0, 0)
    assert pospos2cardinal_direction(you, (0, -1)) == CardinalDirection.North
    assert pospos2cardinal_direction(you, (1, -1)) == CardinalDirection.NorthEast
    assert pospos2cardinal_direction(you, (1, 0)) == CardinalDirection.East
    assert pospos2cardinal_direction(you, (1, 1)) == CardinalDirection.SouthEast
    assert pospos2cardinal_direction(you, (0, 1)) == CardinalDirection.South
    assert pospos2cardinal_direction(you, (-1, 1)) == CardinalDirection.SouthWest
    assert pospos2cardinal_direction(you, (-1, 0)) == CardinalDirection.West
    assert pospos2cardinal_direction(you, (-1, -1)) == CardinalDirection.NorthWest
    assert pospos2cardinal_direction(you, (0, 0)) == CardinalDirection.North
