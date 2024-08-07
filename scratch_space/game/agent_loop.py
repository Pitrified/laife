import sys

import pygame

from laife.agents.player import Player, PlayerState

# Initialize Pygame
pygame.init()

# Set up display
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Minimal Pygame")

# Create the players
player_idle = Player(
    name="inu_idle",
    position=(100, 100),
    player_type="inu",
)
player_think = Player(
    name="inu_think",
    position=(200, 100),
    player_type="inu",
    state=PlayerState.THINKING,
)

# Add the players to a sprite group
all_sprites = pygame.sprite.Group()
all_sprites.add(player_idle)
all_sprites.add(player_think)

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Fill the screen with a color (RGB)
    screen.fill((0, 0, 0))

    # Draw the players
    all_sprites.draw(screen)

    # Update the display
    pygame.display.flip()
