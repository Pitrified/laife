"""PlayerSprite — pygame visual representation of a PlayerAgent."""

import pygame
from pygame.sprite import Sprite

from laife.entities.player_agent import PlayerAgent
from laife.ui.sprites import SpriteLoader


class PlayerSprite(Sprite):
    """Pygame sprite that mirrors the visual state of a PlayerAgent.

    The renderer calls ``sync()`` (or relies on the Sprite.update() hook)
    each frame to pull the latest state and position from the agent without
    the agent ever needing to know about pygame surfaces.
    """

    def __init__(self, agent: PlayerAgent, *groups: pygame.sprite.Group) -> None:
        """Create a sprite for *agent*, optionally adding it to *groups*."""
        super().__init__(*groups)
        self.agent = agent
        self.sprite_loader = SpriteLoader("player", agent.player_type)
        # force an initial sync so image/rect are always valid
        self._last_state = None
        self.sync()

    # ------------------------------------------------------------------
    # Sync helpers
    # ------------------------------------------------------------------

    def sync(self) -> None:
        """Pull state and position from the agent and update pygame image/rect."""
        agent_state = self.agent.state.value
        # only reload the surface when the state actually changes
        if agent_state != self._last_state:
            self.image = self.sprite_loader.load_sprite(agent_state)
            self.rect = self.image.get_rect()
            self._last_state = agent_state
        self.rect.center = self.agent.position

    def update(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003, ARG002
        """Pygame Group.update() hook — delegates to sync()."""
        self.sync()
