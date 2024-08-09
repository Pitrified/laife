import pygame
from pygame.surface import Surface

from laife.config.constants import SPRITES_FOL

INU = {
    "idle": {
        "x": 16,
        "y": 32,
        "width": 74,
        "height": 74,
    },
    "thinking": {
        "x": 177,
        "y": 129,
        "width": 74,
        "height": 74,
    },
}

SPRITES = {
    "inu": INU,
}


class SpriteSheet:
    def __init__(self, sprite_type: str) -> None:
        """Load the sprite sheet."""
        self.sprite_type = sprite_type
        sprite_fp = SPRITES_FOL / f"{self.sprite_type}.png"
        self.sprite_sheet = pygame.image.load(sprite_fp).convert_alpha()

    def get_sprite(self, x, y, width, height) -> Surface:
        """Extract a single sprite from the sprite sheet using subsurface."""
        rect = pygame.Rect(x, y, width, height)
        return self.sprite_sheet.subsurface(rect)

    def get_sprite_state(self, state: str) -> Surface:
        """Extract a sprite state from the sprite sheet."""
        sprite_pos = SPRITES[self.sprite_type][state]
        return self.get_sprite(**sprite_pos)
