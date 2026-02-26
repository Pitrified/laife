"""WorldRunner - pure simulation loop, no pygame dependency."""

import asyncio

from laife.entities.building import Building
from laife.entities.player import Player
from laife.entities.utils.geometry import aabb_collides
from laife.entities.world_channel import WRecBuild
from laife.entities.world_channel import WRecMove
from laife.entities.world_channel import WRecObserve
from laife.entities.world_channel import WReq
from laife.entities.world_channel import WRes
from laife.entities.world_channel import WResStatus
from laife.ui.alog import alg


class WorldRunner:
    """Manages game-logic simulation without any display dependency.

    The runner owns authoritative entity state.  A WorldRenderer can
    observe it to produce visuals, but is not required for the runner
    to operate (enabling headless simulation and testing).
    """

    def __init__(self) -> None:
        """Initialise the runner with empty entity lists and an input queue."""
        # authoritative entity lists (no pygame data structures)
        self.players: list[Player] = []
        self.buildings: list[Building] = []

        # players send world-modification requests through this queue
        self.input_queue: asyncio.Queue[WReq] = asyncio.Queue()

    # ------------------------------------------------------------------
    # Simulation loop
    # ------------------------------------------------------------------

    async def simulate(self) -> None:
        """Process player requests from the input queue indefinitely."""
        alg.log("W: Simulating the world")
        while True:
            alg.log("W: awaiting player input")
            player_input = await self.input_queue.get()
            alg.log(f"W: Got player input: {player_input}")
            wrsp = await self.handle_player_input(player_input)
            self.input_queue.task_done()
            await player_input.response_queue.put(wrsp)
            alg.log("W: Sent response to player")

    async def handle_player_input(self, player_input: WReq) -> WRes:
        """Route the player request to the appropriate handler."""
        match player_input:
            case WRecBuild():
                wrsp = self.add_building(player_input.building)
            case WRecObserve():
                wrsp = self.describe_world()
            case WRecMove():
                wrsp = self.move_player(player_input)
            case _:
                await asyncio.sleep(1)
                wrsp = WRes(
                    WResStatus.ERROR,
                    {"message": f"unknown request {player_input}"},
                )
        return wrsp

    # ------------------------------------------------------------------
    # Entity management
    # ------------------------------------------------------------------

    def add_player(self, player: Player) -> None:
        """Register a player with the world."""
        self.players.append(player)

    def add_building(self, building: Building) -> WRes:
        """Add a building after checking for spatial collisions."""
        for existing in self.buildings:
            if aabb_collides(building.position, building.size, existing.position, existing.size):
                return WRes(
                    WResStatus.ERROR,
                    {"message": "building collides with another building"},
                )
        self.buildings.append(building)
        return WRes(WResStatus.SUCCESS, {"message": "building added"})

    def move_player(self, req: WRecMove) -> WRes:
        """Validate a one-step player move and return success or collision feedback.

        The player's position is NOT mutated here; the player updates itself
        after receiving SUCCESS.
        """
        player_size = req.player.size
        for building in self.buildings:
            if aabb_collides(req.new_position, player_size, building.position, building.size):
                return WRes(
                    WResStatus.ERROR,
                    {"obstacle": str(building), "at": req.new_position},
                )
        for other in self.players:
            if other is req.player:
                continue
            if aabb_collides(req.new_position, player_size, other.position, other.size):
                return WRes(
                    WResStatus.ERROR,
                    {"obstacle": str(other), "at": req.new_position},
                )
        return WRes(WResStatus.SUCCESS, {"new_position": req.new_position})

    def describe_world(self) -> WRes:
        """Return a placeholder world description for the observing player."""
        # TODO: implement real world description
        description = "You are standing in an open field. There are no buildings nearby."
        return WRes(WResStatus.SUCCESS, {"description": description})

    def craft(self) -> None:
        """Craft something (stub)."""
