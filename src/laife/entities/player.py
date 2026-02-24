"""Player entity - agent logic and state, no pygame dependency."""

import asyncio
from enum import StrEnum
import time

from laife.config.types import Position
from laife.entities.action import ActionBuild
from laife.entities.action import ActionCraft
from laife.entities.action import ActionMove
from laife.entities.action import ActionPlan
from laife.entities.action import BaseAction
from laife.entities.utils.directions import CardinalDirection
from laife.entities.world_channel import WReq
from laife.entities.world_channel import WRes
from laife.entities.world_channel import WResStatus
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionHistoryEntry
from laife.llm.mission import MissionStatus
from laife.llm.player_brain import PlayerBrain
from laife.ui.alog import alg


class PlayerState(StrEnum):
    """Possible runtime states for a player."""

    IDLE = "idle"
    THINKING = "thinking"
    MOVING = "moving"


class Player:
    """Pure agent: state, logic, and world communication - no pygame."""

    def __init__(
        self,
        name: str,
        position: Position,
        player_type: str,
        world_input_queue: asyncio.Queue[WReq],
        state: PlayerState = PlayerState.IDLE,
    ) -> None:
        """Create the player.

        The play loop is NOT started here.  The caller is responsible for
        starting it (e.g. via asyncio.create_task or asyncio.gather).
        """
        self.name: str = name
        self.player_type: str = player_type

        # logical state - no sprite side-effects
        self.position: Position = position
        self.state: PlayerState = state

        # communication channels
        self.world_input_queue: asyncio.Queue[WReq] = world_input_queue
        self.input_queue: asyncio.Queue[WRes] = asyncio.Queue()

        # cognition
        self.brain = PlayerBrain()
        self.mission = Mission(
            objective="Build a house",
            status=MissionStatus.ACTIVE,
        )
        self.history = MissionHistory()

    # ------------------------------------------------------------------
    # Agent loop
    # ------------------------------------------------------------------

    async def play(self) -> None:
        """Run the agent decision loop (intended to run as an asyncio task)."""
        while True:
            alg.log(f"PLAYER.play {self.name}: needs to {self.mission}")
            action = await self.think()
            match action:
                case ActionMove() as act:
                    wrsp = await self.move(act)
                case ActionBuild() as act:
                    wrsp = await self.build(act)
                case ActionCraft() as act:
                    wrsp = await self.craft(act)
                case ActionPlan() as act:
                    wrsp = await self.plan(act)
                case _:
                    wrsp = await self.action_error(action)
            he = MissionHistoryEntry(action=action, result=str(wrsp))
            self.history.add_history_entry(he)

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    async def think(self) -> BaseAction:
        """Decide what to do next."""
        self.state = PlayerState.THINKING
        alg.log(f"{self.name} is thinking")
        # placeholder - LLM call will go through self.brain (deferred)
        action = ActionMove(
            reason="I need to move to complete the mission.",
            direction=CardinalDirection.North,
            distance=10,
        )
        # > action = await self.brain.think(self.mission, self.history)
        alg.log(f"PLAYER.play {self.name}: picked {action}")
        self.state = PlayerState.IDLE
        return action

    async def plan(self, action: ActionPlan) -> WRes:
        """Reflect on the mission and plan next steps."""
        alg.log(f"PLAYER.plan {self.name}: planning for {action.reason}")
        self.state = PlayerState.THINKING
        await asyncio.sleep(1)
        alg.log(f"PLAYER.plan {self.name}: planned")
        self.state = PlayerState.IDLE
        return WRes(WResStatus.SUCCESS, {"message": "Planning completed."})

    async def move(self, action: ActionMove) -> WRes:  # noqa: ARG002
        """Move the player."""
        self.state = PlayerState.MOVING
        alg.log(f"PLAYER.move {self.name}: is moving")
        # TODO: delegate move to world for collision detection
        await asyncio.sleep(1)
        alg.log(f"PLAYER.move {self.name}: moved")
        self.state = PlayerState.IDLE
        return WRes(WResStatus.SUCCESS, {"message": "You reached the destination."})

    def move_delta(self, dx: int, dy: int) -> None:
        """Adjust the player's position by delta values."""
        self.position = (self.position[0] + dx, self.position[1] + dy)

    async def build(self, action: ActionBuild) -> WRes:  # noqa: ARG002
        """Prepare and send a build request to the world."""
        await asyncio.sleep(1)
        return WRes(WResStatus.SUCCESS, {"message": "You built the thing."})

    async def craft(self, action: ActionCraft) -> WRes:  # noqa: ARG002
        """Prepare a craft request."""
        await asyncio.sleep(1)
        return WRes(WResStatus.SUCCESS, {"message": "You crafted the thing."})

    async def action_error(self, action: BaseAction) -> WRes:
        """Handle an unknown action type."""
        alg.log(f"PLAYER.play {self.name}: unknown action {action}")
        await asyncio.sleep(1)
        return WRes(WResStatus.ERROR, {"message": f"unknown action {action}"})

    async def world_request(self) -> None:
        """Send a generic request to the world and await the response."""
        alg.log(f"PWR {self.name}: requesting")
        wreq = WReq(response_queue=self.input_queue)
        request_start = time.time()
        alg.log(f"PWR: world input queue len: {self.world_input_queue.qsize()}")
        await self.world_input_queue.put(wreq)
        answer = await self.input_queue.get()
        alg.log(f"PWR player input queue len: {self.input_queue.qsize()}")
        request_end = time.time()
        alg.log(f"PWR {self.name}: got answer {answer} in {request_end - request_start:.6f}s")
        self.input_queue.task_done()

    def __str__(self) -> str:
        """Return a concise human-readable representation of the player."""
        return f"Player {self.name} at {self.position} with state {self.state}"
