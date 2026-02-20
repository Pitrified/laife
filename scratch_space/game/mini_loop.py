"""Minimal pygame + asyncio loop examples for local testing."""

import asyncio
import sys
import time
from typing import NoReturn

import pygame


class Player:
    """A player class."""

    def __init__(self, name: str) -> None:
        """Initialize the player."""
        self.name = name
        self.state = "idle"

    async def think(self) -> None:
        """Think about the next move."""
        self.state = "thinking"
        print(f"PLAYER.think: {self.name} is thinking")
        start_think = time.time()
        await asyncio.sleep(3.5)
        end_think = time.time()
        print(f"PLAYER.think: {self.name} thought in {end_think - start_think:.2f}s")
        self.state = "idle"


async def play(player: Player) -> None:
    """Play the game."""
    while True:
        print(f"PLAY: Playing with {player.name}")
        await player.think()


# initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()


async def main_loop() -> NoReturn:
    """Start the minimal game main loop and spawn player tasks."""
    print("MAIN: Starting game loop")
    players = [Player(f"p{i}") for i in range(5)]
    # keep the reference
    player_tasks = [asyncio.create_task(play(player)) for player in players]  # noqa: F841

    while True:
        # print("MAIN: Running game loop")

        # check for events
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    pygame.quit()
                    sys.exit()

        # pygame update
        screen.fill((0, 0, 0))
        pygame.display.flip()
        # no need to limit the frame rate
        # clock.tick(10)

        # yield control to the event loop
        await asyncio.sleep(0)


# Run the main loop
asyncio.run(main_loop())
