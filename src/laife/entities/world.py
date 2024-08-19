"""A world class."""

import asyncio
import sys
import time

import pygame

from laife.entities.building import Building
from laife.entities.player import Player
from laife.ui.alog import alg


class World:
    """A world class."""

    def __init__(self) -> None:
        """Initialize the world."""
        self.init_renderer()

        # setup the player input queue
        self.input_queue = asyncio.Queue()

        # setup the player and entities groups
        self.players = pygame.sprite.Group()
        self.buildings = pygame.sprite.Group()

    async def simulate(self) -> None:
        """Simulate the agents in the world."""
        alg.log("W: Simulating the world")
        while True:
            alg.log("W: awaiting player input")
            player_input = await self.input_queue.get()
            alg.log(f"W: Got player input: {player_input}")
            # execute the player input
            await asyncio.sleep(1)
            # mark the task as done
            self.input_queue.task_done()
            # pack the answer into an object and send it back to the player
            await player_input["output_queue"].put("ack")
            alg.log("W: Sent ack to player")

    def add_player(self, player: Player) -> None:
        """Add a player to the world."""
        self.players.add(player)

    def add_building(self, building: Building) -> None:
        """Add a building to the world."""
        self.buildings.add(building)

    ## RENDER METHODS

    def init_renderer(self) -> None:
        """Initialize the world renderer."""
        # initialize Pygame
        pygame.init()
        pygame.display.set_caption("lAIfe simulation")
        self.screen = pygame.display.set_mode((1200, 900))
        # set the redraw period to 1 second
        self.redraw_period_sec = 1
        # set the redraw deadline to now so that the world is drawn immediately
        self.redraw_deadline = time.time()
        # start rendering the world
        asyncio.create_task(self.render())

    async def render(self) -> None:
        """Render the world."""
        alg.log("W: Starting rendering loop")
        while True:
            self.check_events()
            self.redraw()
            await asyncio.sleep(0.1)

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
                    self.quit()
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_q:
                            self.quit()

    def quit(self) -> None:
        """Quit the game."""
        alg.log_nowait("W: Quitting the game\n")
        pygame.quit()
        sys.exit()

    def redraw(self) -> None:
        """Draw the world."""
        if not self.should_redraw():
            return
        self.screen.fill((0, 0, 0))
        self.players.draw(self.screen)
        self.buildings.draw(self.screen)
        pygame.display.flip()
        self.reset_deadline()
