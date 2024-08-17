import pygame
from pygame.surface import Surface

from laife.config.constants import SPRITES_FOL

INU_SPRITE_SHEET_COORDS = {
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

SPRITES_SHEET_COORDS = {
    "inu": INU_SPRITE_SHEET_COORDS,
}

INU_STATE_FNS = {
    "idle": "inu_idle_00.png",
    "thinking": "inu_basic_02.png",
    "moving": "inu_idle_back_00.png",
}

STATE_FNS = {
    "inu": INU_STATE_FNS,
}


class SpriteSheet:
    def __init__(self, sprite_type: str) -> None:
        """Load the sprite sheet."""
        self.sprite_type = sprite_type
        sprite_fp = SPRITES_FOL / f"{self.sprite_type}" / f"{self.sprite_type}.png"
        self.sprite_sheet = pygame.image.load(sprite_fp).convert_alpha()

    def get_sprite(self, x, y, width, height) -> Surface:
        """Extract a single sprite from the sprite sheet using subsurface."""
        rect = pygame.Rect(x, y, width, height)
        return self.sprite_sheet.subsurface(rect)

    def get_sprite_state(self, state: str) -> Surface:
        """Extract a sprite state from the sprite sheet."""
        sprite_pos = SPRITES_SHEET_COORDS[self.sprite_type][state]
        return self.get_sprite(**sprite_pos)


class SpriteLoader:
    """A sprite loader class."""

    def __init__(
        self,
        entity_type: str,
        entity_kind: str,
    ) -> None:
        """Initialize the sprite loader.

        * Entity types: player, terrain, tool, building
        * Entity kinds: human, animal, plant, object
        * Entity states: idle, thinking, moving
        """
        self.loaded_sprites = {}
        self.entity_type = entity_type
        self.entity_kind = entity_kind
        self.init_sprite_paths()

    def init_sprite_paths(self) -> None:
        """Return the sprite paths for the requested entity."""
        entity_fol = SPRITES_FOL / self.entity_kind
        entity_fns = STATE_FNS[self.entity_kind]
        self.sprite_paths = {
            state: entity_fol / entity_fns[state] for state in entity_fns
        }

    def load_sprite(self, state: str) -> pygame.Surface:
        """Load a sprite for the requested entity state."""
        if state not in self.loaded_sprites:
            self.loaded_sprites[state] = pygame.image.load(
                self.sprite_paths[state]
            ).convert_alpha()
        return self.loaded_sprites[state]
