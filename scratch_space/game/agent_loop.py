"""Test the agent loop with asyncio and Pygame.

Last working commit:
e033a973a352a5a6b004a45d27ffe09cc3c0425a
"""

import asyncio
from asyncio.queues import Queue
import sys
import time

from loguru import logger as lg
import pygame

from laife.entities.player import Player, PlayerState
from laife.llm.brain import Brain


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
        player.move_delta(dx, dy)
        await asyncio.sleep(delay)


async def player_poll(player: Player) -> None:
    """Poll the player for input."""
    lg.info(f"Polling player {player.name}")
    while not player.dying:
        if player.input_data is not None:
            lg.info(f"Player {player.name} received input: {player.input_data}")
            await player.think()
            player.input_data = None
        await asyncio.sleep(0.25)
    lg.info(f"Player {player.name} is dying")


async def player_queue(player: Player, queue: Queue) -> None:
    while True:
        lg.info("Waiting for input in player_queue")
        input_data = await queue.get()
        lg.info(f"Received {input_data=} in player_queue")
        if input_data is None:
            lg.info("Exiting player_queue")
            break
        player.input_data = input_data
        lg.info("Sent input to player, awaiting think")
        await player.think()
        lg.info("Processed input in player_queue")


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
player_poller = Player(
    name="inu_poll",
    position=(300, 100),
    player_type="inu",
)
player_queuer = Player(
    name="inu_queue",
    position=(400, 100),
    player_type="inu",
)

# Add the players to a sprite group
all_sprites = pygame.sprite.Group()
all_sprites.add(player_idle)
all_sprites.add(player_think)
all_sprites.add(player_poller)
all_sprites.add(player_queuer)

# Throttle the loop
clock = pygame.time.Clock()


def exit_game():
    pygame.quit()
    sys.exit()


async def main_loop():
    lg.info("Starting game loop")
    mover_task = asyncio.create_task(async_player_action(player_idle, 5, 5, 0.7, 10))
    # poller_task = asyncio.create_task(player_poll(player_poller))
    input_queue = Queue()
    queuer_task = asyncio.create_task(player_queue(player_queuer, input_queue))

    # Main game loop
    while True:
        # lg.info("Running game loop")
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    exit_game()
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_q:
                            exit_game()

        # # Can the poller receive input?
        # if player_poller.input_data is None:
        #     lg.info("Sending input to player_poller")
        #     player_poller.input_data = "I love programming."
        #     lg.info("Sent input to player_poller")

        # Can the queuer receive input?
        if player_queuer.input_data is None:
            lg.info("Sending input to player_queuer")
            await input_queue.put("I think, therefore I am.")
            lg.info("Sent input to player_queuer")

        # Fill the screen with a color (RGB)
        screen.fill((0, 0, 0))

        # Draw the players
        all_sprites.draw(screen)

        # Update the display
        pygame.display.flip()

        # # Throttle the loop
        # clock.tick(20)

        # Yield control to the event loop
        await asyncio.sleep(0)


# Run the main loop
asyncio.run(main_loop())
