import asyncio
from enum import Enum
import random
import time

from pygame.sprite import Sprite

from laife.config.types import Position
from laife.entities.player_state import PlayerState
from laife.entities.world_channel import WorldRequest, WorldResponse
from laife.llm.brain import Brain
from laife.llm.mission import Mission
from laife.ui.alog import alg
from laife.ui.sprites import SpriteLoader, SpriteSheet


class Player(Sprite):
    def __init__(
        self,
        name: str,
        position: Position,
        player_type: str,
        world_input_queue: asyncio.Queue[WorldRequest],
        state: PlayerState = PlayerState.IDLE,
    ) -> None:
        super().__init__()

        # save info about the player
        self.name: str = name

        # load the player sprite for this player type
        self.player_type = player_type
        self.sprite_loader = SpriteLoader("player", self.player_type)

        # save the world input queue
        self.world_input_queue: asyncio.Queue[WorldRequest] = world_input_queue

        # the state needs to know the position
        self.position = position
        self.set_state(state)
        self.set_position(position)

        # this is the queue where the player will receive input
        self.input_queue: asyncio.Queue[WorldResponse] = asyncio.Queue()

        # setup the player brain
        self.brain = Brain()

        # the player mission
        self.mission = Mission("Build a house")

        # start the player loop
        asyncio.create_task(self.play())

    async def play(self) -> None:
        """Play the game."""
        while True:
            alg.log(f"PLAYER.play {self.name}: needs to {self.mission}")
            # think about the mission
            action = await self.think()
            # execute the action
            match action:
                case "move":
                    wrsp = await self.move()
                case "request":
                    wrsp = await self.world_request()
                case _:
                    alg.log(f"PLAYER.play {self.name}: unknown action {action}")
                    await asyncio.sleep(1)
                    wrsp = WorldResponse(
                        "error", {"message": f"unknown action {action}"}
                    )
            # gather the feedback of what this action did
            self.mission.add_history_entry(action, str(wrsp))

    async def think(self) -> str:
        """Examine the mission and decide what to do."""
        self.set_state(PlayerState.THINKING)

        alg.log(f"{self.name} is thinking")
        think_start = time.time()
        alg.log(f"Think start: {think_start}")
        action = await self.brain.think("Should I rest or move?")
        think_end = time.time()
        alg.log(f"Brain think time: {think_end-think_start:.6f}")
        alg.log(
            f"PLAYER.think: {self.name} thought in {think_end-think_start:.2f}s"
            f" and decided to {action}"
        )

        # for now it's just a random decision
        # options = ["move", "request"]
        # action = random.choice(options)
        action = "request"
        alg.log(f"PLAYER.play {self.name}: picked {action}")

        self.set_state(PlayerState.IDLE)
        return action

    async def move(self) -> WorldResponse:
        """Move the player."""
        self.set_state(PlayerState.MOVING)
        alg.log(f"PLAYER.move {self.name}: is moving")
        # FIXME - replace with actual movement logic with move_delta loop
        await asyncio.sleep(1)
        alg.log(f"PLAYER.move {self.name}: moved")
        self.set_state(PlayerState.IDLE)
        wrsp = WorldResponse("ok", {"message": "You reached the destination."})
        return wrsp

    def move_delta(self, dx: int, dy: int) -> None:
        new_position = (self.position[0] + dx, self.position[1] + dy)
        self.set_position(new_position)

    def set_position(self, position: Position) -> None:
        self.position = position
        self.rect.center = self.position

    def set_state(self, state: PlayerState) -> None:
        self.state = state
        self.image = self.sprite_loader.load_sprite(self.state.value)
        self.rect = self.image.get_rect()
        # call set_position to update the rect position
        self.set_position(self.position)

    async def world_request(self) -> None:
        """Request something from the world."""
        alg.log(f"PWR {self.name}: requesting")
        # send a request to the world
        wreq = WorldRequest(
            response_queue=self.input_queue,
            request_type="test_request",
            request_data={},
        )
        request_start = time.time()
        alg.log(f"PWR: world input queue len: {self.world_input_queue.qsize()}")
        await self.world_input_queue.put(wreq)
        # wait for the answer
        answer = await self.input_queue.get()
        alg.log(f"PWR player input queue len: {self.input_queue.qsize()}")
        request_end = time.time()
        request_time = request_end - request_start
        alg.log(f"PWR {self.name}: got answer {answer} in {request_time:.6f}s")
        self.input_queue.task_done()

    def __str__(self) -> str:
        return f"Player {self.name} at {self.position} with state {self.state}"
