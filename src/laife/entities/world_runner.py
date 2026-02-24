"""WorldRunner — pure simulation loop, no pygame dependency."""

import asyncio

from laife.entities.building_data import BuildingData
from laife.entities.geometry import aabb_collides
from laife.entities.player_agent import PlayerAgent
from laife.entities.world_channel import WRecBuild
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
        self.agents: list[PlayerAgent] = []
        self.buildings: list[BuildingData] = []

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

    def add_player(self, agent: PlayerAgent) -> None:
        """Register a player agent with the world."""
        self.agents.append(agent)

    def add_building(self, building: BuildingData) -> WRes:
        """Add a building after checking for spatial collisions."""
        for existing in self.buildings:
            if aabb_collides(building.position, building.size, existing.position, existing.size):
                return WRes(
                    WResStatus.ERROR,
                    {"message": "building collides with another building"},
                )
        self.buildings.append(building)
        return WRes(WResStatus.SUCCESS, {"message": "building added"})

    def move_player(self) -> None:
        """Move the player (stub)."""

    def craft(self) -> None:
        """Craft something (stub)."""
