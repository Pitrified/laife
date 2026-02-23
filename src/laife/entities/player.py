"""Player entity and behavior for the game."""

import asyncio
import time

from pygame.sprite import Sprite

from laife.config.types import Position
from laife.entities.action import Action
from laife.entities.action import ActionBuild
from laife.entities.action import ActionCraft
from laife.entities.action import ActionMove
from laife.entities.player_state import PlayerState
from laife.entities.world_channel import WorldRequest
from laife.entities.world_channel import WorldResponse
from laife.entities.world_channel import WorldResponseStatus
from laife.llm.brain import Brain
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionHistoryEntry
from laife.llm.mission import MissionStatus
from laife.llm.mission import MissionStep
from laife.llm.mission import MissionType
from laife.ui.alog import alg
from laife.ui.directions import CardinalDirection
from laife.ui.sprites import SpriteLoader


class Player(Sprite):
    """Represents a player with state, brain, and world interaction."""

    def __init__(
        self,
        name: str,
        position: Position,
        player_type: str,
        world_input_queue: asyncio.Queue[WorldRequest],
        state: PlayerState = PlayerState.IDLE,
    ) -> None:
        """Create a new player with initial state and background tasks."""
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
        ms = MissionStep(
            mission_type=MissionType.BUILD,
            objective="Build a house",
            status=MissionStatus.ACTIVE,
        )
        self.mission = Mission.from_step(ms)
        # the player history
        self.history = MissionHistory()

        # start the player loop
        self.play_task = asyncio.create_task(self.play())

    async def play(self) -> None:
        """Play the game."""
        while True:
            alg.log(f"PLAYER.play {self.name}: needs to {self.mission}")
            # TODO: add exploration step
            # think about the mission
            action = await self.think()
            # execute the action
            match action:
                case ActionMove():
                    action_handler = self.move
                case ActionBuild():
                    action_handler = self.build
                case ActionCraft():
                    action_handler = self.craft
                case _:
                    action_handler = self.action_error
            wrsp = await action_handler(action)
            # save the feedback of what this action did
            he = MissionHistoryEntry(action=action, result=str(wrsp))
            self.history.add_history_entry(he)

    async def think(self) -> Action:
        """Examine the mission and decide what to do."""
        self.set_state(PlayerState.THINKING)
        alg.log(f"{self.name} is thinking")

        # TODO: - replace with actual thinking logic
        # > think_start = time.time()
        # > alg.log(f"Think start: {think_start}")
        # > action = await self.brain.think("Should I rest or move?")
        # > think_end = time.time()
        # > alg.log(f"Brain think time: {think_end-think_start:.6f}")
        # > alg.log(
        # >     f"PLAYER.think: {self.name} thought in {think_end-think_start:.2f}s"
        # >     f" and decided to {action}"
        # > )

        # for now it's just a random decision
        # > options = ["move", "request"]
        # > action = random.choice(options)

        # actually send the object, static
        am = ActionMove(
            direction=CardinalDirection.North,
            distance=10,
        )
        action = Action(
            act=am,
            reason="I need to move to complete the mission.",
        )

        alg.log(f"PLAYER.play {self.name}: picked {action}")
        self.set_state(PlayerState.IDLE)
        return action

    async def move(self, action: Action) -> WorldResponse:
        """Move the player."""
        self.set_state(PlayerState.MOVING)
        alg.log(f"PLAYER.move {self.name}: is moving")

        am: ActionMove = action.get_action_move()  # noqa: F841

        # TODO: the move should also be delegated to the world
        # the think method should return an action
        # here we package it into a WRMove object and send it to the world
        # and the world should handle the move, so we can collision detect
        # ? package self into a WRMove object and send it to the world,
        #   and the world will progressively move the player
        # ? or do we receive the step from the world and move the player here?

        # TODO: replace with actual movement logic with move_delta loop
        wrsp = WorldResponse(
            WorldResponseStatus.SUCCESS,
            {"message": "You reached the destination."},
        )
        await asyncio.sleep(1)

        alg.log(f"PLAYER.move {self.name}: moved")
        self.set_state(PlayerState.IDLE)
        return wrsp

    def move_delta(self, dx: int, dy: int) -> None:
        """Adjust the player's position by delta values."""
        new_position = (self.position[0] + dx, self.position[1] + dy)
        self.set_position(new_position)

    async def build(self, action: Action) -> WorldResponse:  # noqa: ARG002
        """Prepare the build request and send it to the world."""
        wrsp = WorldResponse(WorldResponseStatus.SUCCESS, {"message": "You built the thing."})
        await asyncio.sleep(1)
        return wrsp

    async def craft(self, action: Action) -> WorldResponse:  # noqa: ARG002
        """Prepare the craft request and send it to the world."""
        wrsp = WorldResponse(WorldResponseStatus.SUCCESS, {"message": "You crafted the thing."})
        await asyncio.sleep(1)
        return wrsp

    async def action_error(self, action: Action) -> WorldResponse:
        """Handle an unknown action."""
        wrsp = await self.action_error(action)
        alg.log(f"PLAYER.play {self.name}: unknown action {action}")
        await asyncio.sleep(1)
        wrsp = WorldResponse(WorldResponseStatus.ERROR, {"message": f"unknown action {action}"})
        return wrsp

    async def world_request(self) -> None:
        """Request something from the world."""
        alg.log(f"PWR {self.name}: requesting")
        # send a request to the world
        wreq = WorldRequest(response_queue=self.input_queue)
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

    ## RENDER METHODS

    def set_position(self, position: Position) -> None:
        """Set the player's position and update rendering rect."""
        self.position = position
        self.rect.center = self.position

    def set_state(self, state: PlayerState) -> None:
        """Update the player's state and refresh sprite/image."""
        self.state = state
        self.image = self.sprite_loader.load_sprite(self.state.value)
        self.rect = self.image.get_rect()
        # call set_position to update the rect position
        self.set_position(self.position)

    def __str__(self) -> str:
        """Return a concise human-readable representation of the player."""
        return f"Player {self.name} at {self.position} with state {self.state}"
