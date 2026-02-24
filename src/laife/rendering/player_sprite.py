"""PlayerSprite - pygame visual representation of a Player."""

import pygame
from pygame.sprite import Sprite

from laife.entities.player import Player
from laife.rendering.sprites import SpriteLoader


class PlayerSprite(Sprite):
    """Pygame sprite that mirrors the visual state of a Player.

    The renderer calls ``sync()`` (or relies on the Sprite.update() hook)
    each frame to pull the latest state and position from the player without
    the player ever needing to know about pygame surfaces.
    """

    def __init__(self, player: Player, *groups: pygame.sprite.Group) -> None:
        """Create a sprite for *player*, optionally adding it to *groups*."""
        super().__init__(*groups)
        self.player = player
        self.sprite_loader = SpriteLoader("player", player.player_type)
        # force an initial sync so image/rect are always valid
        self._last_state = None
        self.sync()

    # ------------------------------------------------------------------
    # Sync helpers
    # ------------------------------------------------------------------

    def sync(self) -> None:
        """Pull state and position from the player and update pygame image/rect."""
        player_state = self.player.state.value
        # only reload the surface when the state actually changes
        if player_state != self._last_state:
            self.image = self.sprite_loader.load_sprite(player_state)
            self.rect = self.image.get_rect()
            self._last_state = player_state
        self.rect.center = self.player.position

    def update(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003, ARG002
        """Pygame Group.update() hook - delegates to sync()."""
        self.sync()
