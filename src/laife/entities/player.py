import asyncio
from enum import Enum
import random
import time

from pygame.sprite import Sprite

from laife.entities.player_state import PlayerState
from laife.llm.brain import Brain
from laife.ui.alog import alg
from laife.ui.sprites import SpriteLoader, SpriteSheet


class Player(Sprite):
    def __init__(
        self,
        name: str,
        position: tuple[int, int],
        player_type: str,
        world_input_queue: asyncio.Queue,
        state: PlayerState = PlayerState.IDLE,
    ) -> None:
        super().__init__()

        # save info about the player
        self.name: str = name

        # load the player sprite for this player type
        self.player_type = player_type
        self.sprite_loader = SpriteLoader("player", self.player_type)

        # save the world input queue
        self.world_input_queue = world_input_queue

        # the state needs to know the position
        self.position = position
        self.set_state(state)
        self.set_position(position)

        # this is the queue where the player will receive input
        self.input_queue = asyncio.Queue()

        # setup the player brain
        self.brain = Brain()

        # the player mission
        self.mission = "rest"

        # start the player loop
        asyncio.create_task(self.play())

    def move_delta(self, dx: int, dy: int) -> None:
        new_position = (self.position[0] + dx, self.position[1] + dy)
        self.set_position(new_position)

    async def move(self) -> None:
        """Move the player."""
        self.set_state(PlayerState.MOVING)
        alg.log(f"PLAYER.move {self.name}: is moving")
        # FIXME - replace with actual movement logic with move_delta
        await asyncio.sleep(1)
        alg.log(f"PLAYER.move {self.name}: moved")
        self.set_state(PlayerState.IDLE)
        self.mission = "rest"

    async def think(self) -> None:
        self.set_state(PlayerState.THINKING)
        alg.log(f"{self.name} is thinking")
        think_start = time.time()
        alg.log(f"Think start: {think_start}")
        self.mission = await self.brain.think("Should I rest or move?")
        think_end = time.time()
        alg.log(f"Brain think time: {think_end-think_start:.6f}")
        alg.log(
            f"PLAYER.think: {self.name} thought in {think_end-think_start:.2f}s"
            f" and decided to {self.mission}"
        )
        self.set_state(PlayerState.IDLE)

    def set_position(self, position: tuple[int, int]) -> None:
        self.position = position
        self.rect.center = self.position

    def set_state(self, state: PlayerState) -> None:
        self.state = state
        self.image = self.sprite_loader.load_sprite(self.state.value)
        self.rect = self.image.get_rect()
        self.set_position(self.position)

    async def execute_mission(self) -> None:
        """Execute the current mission."""
        match self.mission:
            case "move":
                await self.move()
            case _:
                alg.log(f"PLAYER.execute_mission {self.name}: doing {self.mission}")

    async def world_request(self) -> None:
        """Request something from the world."""
        alg.log(f"PWR {self.name}: requesting")
        # send a request to the world
        request = {"player.name": self.name, "output_queue": self.input_queue}
        request_start = time.time()
        alg.log(f"PWR: world input queue len: {self.world_input_queue.qsize()}")
        await self.world_input_queue.put(request)
        # wait for the answer
        answer = await self.input_queue.get()
        alg.log(f"PWR player input queue len: {self.input_queue.qsize()}")
        request_end = time.time()
        request_time = request_end - request_start
        alg.log(f"PWR {self.name}: got answer {answer} in {request_time:.6f}s")
        self.input_queue.task_done()

    async def play(self) -> None:
        """Play the game."""
        while True:
            alg.log(f"PLAYER.play {self.name}: needs to {self.mission}")
            # think about the mission
            # for now it's just a random decision
            options = ["execute", "think", "move", "request"]
            # input_cmd = random.choice(options)
            input_cmd = "request"
            alg.log(f"PLAYER.play {self.name}: picked {input_cmd}")
            match input_cmd:
                case "execute":
                    await self.execute_mission()
                case "think":
                    await self.think()
                case "move":
                    await self.move()
                case "request":
                    await self.world_request()

    def __str__(self) -> str:
        return f"Player {self.name} at {self.position} with state {self.state}"
