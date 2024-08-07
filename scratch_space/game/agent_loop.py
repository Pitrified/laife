import asyncio
import sys
import time

import pygame
from loguru import logger as lg

from laife.agents.player import Player, PlayerState


# Define an asynchronous function for player actions
async def async_player_action(
    player: Player,
    dx: int,
    dy: int,
    delay: float,
    movement_count: int,
) -> None:
    lg.info(f"Moving player {player.name} {movement_count} times")
    for i in range(movement_count):
        lg.debug(f"Moving player {player.name}, {i:3d} by {dx}, {dy}")
        player.move(dx, dy)
        await asyncio.sleep(delay)


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

# Throttle the loop
clock = pygame.time.Clock()


def exit_game():
    pygame.quit()
    sys.exit()


async def main_loop():
    lg.info("Starting game loop")
    player_task = asyncio.create_task(async_player_action(player_idle, 5, 5, 0.3, 10))

    # Main game loop
    while True:
        lg.info("Running game loop")
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    exit_game()
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_q:
                            exit_game()

        # Fill the screen with a color (RGB)
        screen.fill((0, 0, 0))

        # Draw the players
        all_sprites.draw(screen)

        # Update the display
        pygame.display.flip()

        # Throttle the loop
        clock.tick(5)

        # Yield control to the event loop
        await asyncio.sleep(0)


# Run the main loop
asyncio.run(main_loop())
