"""BuildingSprite — pygame visual representation of a BuildingData."""

import pygame
import pygame.freetype
from pygame.sprite import Sprite

from laife.entities.building_data import BuildingData
from laife.ui.alog import alg


class BuildingSprite(Sprite):
    """Pygame sprite that renders a BuildingData entity."""

    def __init__(self, building: BuildingData, *groups: pygame.sprite.Group) -> None:
        """Create a sprite surface for the given building."""
        super().__init__(*groups)
        self.building = building
        alg.log(f"BUILD: Creating sprite for {self.building.name}")
        self._create_surface()

    def _create_surface(self) -> None:
        """Build the pygame Surface and Rect from the building data."""
        bgcolor = (255, 100, 100)

        font = pygame.freetype.SysFont("Helvetica", 16)
        surf, rect = font.render(
            self.building.name,
            fgcolor=(100, 255, 100),
            bgcolor=bgcolor,
        )

        surf_end = pygame.Surface(self.building.size)
        surf_end.fill(bgcolor)

        blit_x = (self.building.size[0] - rect.width) // 2
        blit_y = (self.building.size[1] - rect.height) // 2
        surf_end.blit(surf, (blit_x, blit_y))

        self.image = surf_end
        self.rect = self.image.get_rect()
        self.rect.topleft = self.building.position
