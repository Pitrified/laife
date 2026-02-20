"""Building entity module."""

import pygame
import pygame.freetype
from pygame.sprite import Sprite

from laife.config.types import Position
from laife.config.types import Size
from laife.ui.alog import alg
from laife.ui.directions import pospos2cardinal_direction

BUILDING_TYPES = ["house", "farm", "factory"]
BUILDING_DESCRIPTIONS = {
    "house": "A place to rest safely.",
    "farm": "A place to grow food.",
    "factory": "A place to make things.",
}


class Building(Sprite):
    """A building class."""

    def __init__(
        self,
        name: str,
        building_type: str,
        description: str | None,
        position: Position,
        size: Size,
        *groups: pygame.sprite.Group,
    ) -> None:
        """Initialize the building."""
        super().__init__(*groups)
        self.name = name
        self.building_type = building_type
        self.description = description
        self.position = position
        self.size = size
        self.create_sprite()

        alg.log(f"BUILD: Created building {self.name} at {self.position}")

    def __str__(self) -> str:
        """Return the string representation of the building."""
        return f"Building {self.name} at {self.position}"

    def create_sprite(self) -> None:
        """Create the sprite for the building."""
        alg.log(f"BUILD: Creating sprite for {self.name}")
        bgcolor = (255, 100, 100)

        # render the name onto a surface
        font = pygame.freetype.SysFont("Helvetica", 16)
        surf, rect = font.render(
            self.name,
            fgcolor=(100, 255, 100),
            bgcolor=bgcolor,
        )

        # create a destination surface
        surf_end = pygame.Surface(self.size)
        surf_end.fill(bgcolor)

        # blit the name onto the destination surface
        blit_x = (self.size[0] - rect.width) // 2
        blit_y = (self.size[1] - rect.height) // 2
        surf_end.blit(surf, (blit_x, blit_y))

        # set the sprite surface and rect
        self.image = surf_end
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position

    def to_prompt(self, pov_pos: Position | None = None) -> str:
        """Return a prompt representation of the building."""
        gen_desc = BUILDING_DESCRIPTIONS[self.building_type]
        p = f"{self.name}: {gen_desc}"
        if self.description is not None:
            p += f"\nNote about this specific {self.building_type}: {self.description}"
        if pov_pos is not None:
            self_cardinal = pospos2cardinal_direction(pov_pos, self.position)
            p += f"\nIt is located to the {self_cardinal.value}."
        else:
            p += f"\nIt is located at {self.position}."
        return p
