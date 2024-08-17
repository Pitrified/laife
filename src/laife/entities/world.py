"""A world class."""

import asyncio
import random
import sys
import time

import pygame

from laife.entities.player import Player
from laife.entities.player_state import PlayerState
from laife.ui.alog import alg


class World:
    """A world class."""

    def __init__(self) -> None:
        """Initialize the world."""
        self.init_renderer()
        self.players = pygame.sprite.Group()
        self.add_player()
        self.add_prob = 0.01
        self.max_players = 1

    async def main_loop(self) -> None:
        """Run the main loop."""
        alg.log("W: Starting game loop")
        while True:
            alg.log("W: Running game loop")
            await self.simulate()
            self.render()
            await asyncio.sleep(0.1)

    async def simulate(self) -> None:
        """Simulate the agents in the world."""
        # alg.log("SIMULATE: Simulating the world")
        for player in self.players:
            # find an idle player
            if player.state != PlayerState.IDLE:
                continue
            # an idle player should have no input in the queue
            if not player.input_queue.empty():
                alg.log(f"SIMULATE: {player.name} is idle but has input")
                continue
            # this would be the place where the WORLD decides what to do
            if random.randint(0, 1):
                alg.log(f"SIMULATE: Adding think to {player.name}")
                await player.input_queue.put("think")
            else:
                alg.log(f"SIMULATE: Adding execute to {player.name}")
                await player.input_queue.put("execute")
        if len(self.players) < self.max_players and random.random() < self.add_prob:
            alg.log(f"SIMULATE: Adding a player {self.add_prob}")
            self.add_player()
            self.add_prob /= 2

    def render(self) -> None:
        """Render the world."""
        self.check_events()
        self.redraw()

    def add_player(self) -> None:
        """Add a player to the world."""
        player = Player(
            f"p{len(self.players)}",
            position=(random.randint(0, 800), random.randint(0, 600)),
            player_type="inu",
        )
        self.players.add(player)
        asyncio.create_task(player.play())

    def init_renderer(self) -> None:
        """Initialize the world renderer."""
        # initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        # set the redraw period to 1 second
        self.redraw_period_sec = 1
        # set the redraw deadline to now so that the world is drawn immediately
        self.redraw_deadline = time.time()

    def reset_deadline(self) -> None:
        """Reset the redraw deadline."""
        self.redraw_deadline = time.time() + self.redraw_period_sec

    def should_redraw(self) -> bool:
        """Check if the screen should be redrawn."""
        return time.time() > self.redraw_deadline

    def check_events(self) -> None:
        """Check for events."""
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    def redraw(self) -> None:
        """Draw the world."""
        if not self.should_redraw():
            return
        self.screen.fill((0, 0, 0))
        self.players.draw(self.screen)
        pygame.display.flip()
        self.reset_deadline()
