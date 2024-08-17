"""Test the directions module."""

import pytest

from laife.ui.directions import Cardinal, pospos2cardinal


def test_pospos2cardinal():
    """Test that pospos2cardinal works."""
    p1 = (0, 0)
    assert pospos2cardinal(p1, (0, 1)) == Cardinal.North
    assert pospos2cardinal(p1, (1, 1)) == Cardinal.NorthEast
    assert pospos2cardinal(p1, (1, 0)) == Cardinal.East
    assert pospos2cardinal(p1, (1, -1)) == Cardinal.SouthEast
    assert pospos2cardinal(p1, (0, -1)) == Cardinal.South
    assert pospos2cardinal(p1, (-1, -1)) == Cardinal.SouthWest
    assert pospos2cardinal(p1, (-1, 0)) == Cardinal.West
    assert pospos2cardinal(p1, (-1, 1)) == Cardinal.NorthWest
    assert pospos2cardinal(p1, (0, 0)) == Cardinal.North
