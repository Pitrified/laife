import asyncio
import random
import sys
import time
from typing import NoReturn

from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import pygame

from laife.config.constants import LANGCHAIN_CACHE_DB
from laife.config.credentials import OPENAI_API_KEY
from laife.ui.alog import alg

set_llm_cache(SQLiteCache(database_path=str(LANGCHAIN_CACHE_DB)))


class Brain:
    """A brain class."""

    def __init__(self) -> None:
        """Initialize the brain."""
        # self.llm = ChatOpenAI(
        #     model="gpt-4o-mini",
        #     temperature=0,
        #     max_tokens=30,
        #     timeout=None,
        #     max_retries=2,
        #     api_key=OPENAI_API_KEY,
        # )
        self.llm = ChatOllama(
            model="phi3",
            temperature=0,
            num_predict=30,
        )

    async def think(self, query: str) -> str:
        # return await self.naive_think(query)
        return await self.llm_think(query)

    async def naive_think(self, query: str) -> str:
        """Randomly think about the next move."""
        await asyncio.sleep(2.5)
        if random.randint(0, 1):
            return "move"
        return "rest"

    async def llm_think(self, query: str) -> str:
        """Use the language model to think about the next move."""
        alg.log(f"BRAIN.llm_think: {query}")
        res = await self.llm.ainvoke(query)
        res_pretty = res.pretty_repr()
        alg.log(f"BRAIN.llm_think: {res}")
        return "move" if "move" in res_pretty else "rest"


class Player:
    """A player class."""

    def __init__(self, name: str) -> None:
        """Initialize the player."""
        self.name = name
        self.state = "idle"
        self.mission = "rest"
        self.input_queue = asyncio.Queue(1)
        self.brain = Brain()

    async def think(self) -> None:
        """Think about the next move."""
        self.state = "thinking"
        alg.log(f"PLAYER.think: {self.name} is thinking")
        start_think = time.time()
        self.mission = await self.brain.think("Should I rest or move?")
        end_think = time.time()
        alg.log(
            f"PLAYER.think: {self.name} thought in {end_think-start_think:.2f}s"
            f" and decided to {self.mission}"
        )
        self.state = "idle"

    async def move(self) -> None:
        """Move the player."""
        self.state = "moving"
        alg.log(f"PLAYER.move {self.name}: is moving")
        await asyncio.sleep(1)
        alg.log(f"PLAYER.move {self.name}: moved")
        self.state = "idle"
        self.mission = "rest"

    async def execute_mission(self) -> None:
        """Execute the current mission."""
        match self.mission:
            case "move":
                await self.move()
            case _:
                alg.log(f"PLAYER.execute_mission {self.name}: doing {self.mission}")

    async def play(self) -> None:
        """Play the game."""
        while True:
            alg.log(f"PLAYER.play {self.name}: awaiting input")
            input_cmd = await self.input_queue.get()
            alg.log(f"PLAYER.play {self.name}: received input {input_cmd}")
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
        self.wr = WorldRenderer()
        self.players = []
        self.add_player()
        self.add_prob = 0.01

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
            if player.state != "idle":
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
        if len(self.players) < 1 and random.random() < self.add_prob:
            alg.log(f"SIMULATE: Adding a player {self.add_prob}")
            self.add_player()
            self.add_prob /= 2

    def render(self) -> None:
        """Render the world."""
        self.wr.render()

    def add_player(self) -> None:
        """Add a player to the world."""
        player = Player(f"p{len(self.players)}")
        self.players.append(player)
        asyncio.create_task(player.play())


class WorldRenderer:
    """A world renderer class."""

    def __init__(self) -> None:
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
        pygame.display.flip()
        self.reset_deadline()

    def render(self) -> None:
        """Render the world."""
        self.check_events()
        self.redraw()


async def main() -> NoReturn:
    """Main function."""
    world = World()
    await world.main_loop()


if __name__ == "__main__":
    # Run the main loop
    asyncio.run(main())
