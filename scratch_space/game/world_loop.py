import asyncio
import random
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
        self.mission = "rest"
        self.input_queue = asyncio.Queue()

    async def think(self) -> None:
        """Think about the next move."""
        self.state = "thinking"
        print(f"PLAYER.think: {self.name} is thinking")
        start_think = time.time()
        await asyncio.sleep(3.5)
        end_think = time.time()
        print(f"PLAYER.think: {self.name} thought in {end_think-start_think:.2f}s")
        # randomly select a mission
        if random.randint(0, 1):
            print(f"PLAYER.think: {self.name} decided to move")
            self.mission = "move"
        self.state = "idle"

    async def move(self) -> None:
        """Move the player."""
        self.state = "moving"
        print(f"PLAYER.move {self.name}: is moving")
        await asyncio.sleep(1)
        print(f"PLAYER.move {self.name}: moved")
        self.state = "idle"
        self.mission = "rest"

    async def execute_mission(self) -> None:
        """Execute the current mission."""
        match self.mission:
            case "move":
                await self.move()
            case _:
                print(f"PLAYER.execute_mission {self.name}: doing {self.mission}")

    async def play(self) -> None:
        """Play the game."""
        while True:
            print(f"PLAYER.play {self.name}: awaiting input")
            input_cmd = await self.input_queue.get()
            print(f"PLAYER.play {self.name}: received input {input_cmd}")
            match input_cmd:
                case "execute":
                    await self.execute_mission()
                case "think":
                    await self.think()
                case "move":
                    await self.move()


class World:
    """A world class."""

    def __init__(self) -> None:
        """Initialize the world."""
        self.players = []
        self.player_tasks = []
        self.add_player()
        self.add_prob = 0.001

    async def simulate(self) -> None:
        """Simulate the world."""
        while True:
            # print("SIMULATE: Simulating the world")
            for player in self.players:
                if player.state == "idle":
                    if not player.input_queue.empty():
                        print(f"SIMULATE: {player.name} is idle but has input")
                        continue
                    # this would be the place where the WORLD decides what to do
                    if random.randint(0, 1):
                        print(f"SIMULATE: Adding think to {player.name}")
                        await player.input_queue.put("think")
                    else:
                        print(f"SIMULATE: Adding execute to {player.name}")
                        await player.input_queue.put("execute")
            if random.random() < self.add_prob:
                print(f"SIMULATE: Adding a player {self.add_prob}")
                self.add_player()
                self.add_prob /= 2
            await asyncio.sleep(0)

    def add_player(self) -> None:
        """Add a player to the world."""
        player = Player(f"p{len(self.players)}")
        self.players.append(player)
        self.player_tasks.append(asyncio.create_task(player.play()))


# initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()


async def main_loop() -> NoReturn:
    print("MAIN: Starting game loop")
    world = World()
    asyncio.create_task(world.simulate())

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

        # yield control to the event loop
        await asyncio.sleep(0)


# Run the main loop
asyncio.run(main_loop())
