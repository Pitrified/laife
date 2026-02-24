"""Player entity module — re-exports for backward compatibility.

New code should import directly from:
  laife.entities.player_agent  (PlayerAgent)
  laife.entities.player_sprite (PlayerSprite)
"""

from laife.entities.player_agent import PlayerAgent
from laife.entities.player_sprite import PlayerSprite
from laife.entities.player_state import PlayerState

# Alias so that ``from laife.entities.player import Player`` keeps working.
Player = PlayerAgent

__all__ = [
    "Player",
    "PlayerAgent",
    "PlayerSprite",
    "PlayerState",
]

# ---- original implementation has moved to player_agent.py / player_sprite.py ----

_MOVED = True
