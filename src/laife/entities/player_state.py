"""Player state enumeration used to control behaviour and rendering."""

from enum import Enum


class PlayerState(Enum):
    """Possible runtime states for a player."""

    IDLE = "idle"
    THINKING = "thinking"
    MOVING = "moving"
