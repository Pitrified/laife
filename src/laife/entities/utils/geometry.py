"""Geometry on the world's integer pixel grid."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from laife.config.types import Position
    from laife.config.types import Size


def aabb_collides(
    pos_a: Position,
    size_a: Size,
    pos_b: Position,
    size_b: Size,
) -> bool:
    """Return True when two axis-aligned rectangles overlap.

    Positions are (left, top) and sizes are (width, height), in world pixels.
    """
    ax1, ay1 = pos_a
    ax2, ay2 = ax1 + size_a[0], ay1 + size_a[1]
    bx1, by1 = pos_b
    bx2, by2 = bx1 + size_b[0], by1 + size_b[1]
    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1
