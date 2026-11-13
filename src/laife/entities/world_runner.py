"""WorldRunner - pure simulation loop, no pygame dependency."""

import asyncio
from typing import TYPE_CHECKING

from llm_core.prompts.prompt_loader import PromptLoaderConfig

from laife.entities.utils.geometry import aabb_collides
from laife.entities.world_channel import WRecBuild
from laife.entities.world_channel import WRecComplete
from laife.entities.world_channel import WRecCraft
from laife.entities.world_channel import WRecInteract
from laife.entities.world_channel import WRecMove
from laife.entities.world_channel import WRecObserve
from laife.entities.world_channel import WReq
from laife.entities.world_channel import WRes
from laife.entities.world_channel import WResBuild
from laife.entities.world_channel import WResComplete
from laife.entities.world_channel import WResCraft
from laife.entities.world_channel import WResError
from laife.entities.world_channel import WResInteract
from laife.entities.world_channel import WResMoveStep
from laife.entities.world_channel import WResObserve
from laife.entities.world_channel import WResStatus
from laife.entities.world_judge import WorldJudge
from laife.entities.world_judge import WorldJudgeConfig
from laife.entities.world_map_observation import NearbyEntity
from laife.entities.world_map_observation import WorldMapObservation
from laife.entities.world_map_observation import euclidean
from laife.meta.log_events import EVT_WORLD_REQUEST
from laife.meta.logger import slog
from laife.params.laife_params import get_laife_params
from laife.ui.alog import alg

if TYPE_CHECKING:
    from llm_core.chat.config.base import ChatConfig

    from laife.config.types import Position
    from laife.entities.building import Building
    from laife.entities.player import Player
    from laife.entities.terrain import Terrain


class WorldRunner:
    """Manages game-logic simulation without any display dependency.

    The runner owns authoritative entity state.  A WorldRenderer can
    observe it to produce visuals, but is not required for the runner
    to operate (enabling headless simulation and testing).
    """

    def __init__(self, chat_config: ChatConfig | None = None) -> None:
        """Initialise the runner with empty entity lists and an input queue.

        *chat_config* feeds the build, craft and complete judges; ``None``
        takes ``llm_services.chat.default``.
        """
        # authoritative entity lists (no pygame data structures)
        self.players: list[Player] = []
        self.buildings: list[Building] = []
        self.terrains: list[Terrain] = []

        # players send world-modification requests through this queue
        self.input_queue: asyncio.Queue[WReq] = asyncio.Queue()

        # LLM judge for build, craft and complete requests
        laife_params = get_laife_params()
        if chat_config is None:
            chat_config = laife_params.llm_services.chat.default
        prompts_fol = laife_params.paths.prompts_fol
        self.judge = WorldJudge(
            WorldJudgeConfig(
                chat_config=chat_config,
                build_prompt=PromptLoaderConfig(
                    base_prompt_fol=prompts_fol, prompt_name="world_judge_build"
                ),
                craft_prompt=PromptLoaderConfig(
                    base_prompt_fol=prompts_fol, prompt_name="world_judge_craft"
                ),
                complete_prompt=PromptLoaderConfig(
                    base_prompt_fol=prompts_fol, prompt_name="world_judge_complete"
                ),
            )
        )

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
            slog.bind(
                event=EVT_WORLD_REQUEST,
                player=player_input.player_name,
                turn=player_input.turn,
                kind=type(player_input).__name__,
            ).info(EVT_WORLD_REQUEST)
            # The judges' LLM calls are logged as the requester's.
            with slog.contextualize(player=player_input.player_name, turn=player_input.turn):
                wrsp = await self.handle_player_input(player_input)
            self.input_queue.task_done()
            await player_input.response_queue.put(wrsp)
            alg.log("W: Sent response to player")

    async def handle_player_input(self, player_input: WReq) -> WRes:
        """Route the player request to the appropriate handler."""
        match player_input:
            case WRecBuild():
                wrsp = await self.judge_and_build(player_input)
            case WRecCraft():
                wrsp = await self.judge_craft(player_input)
            case WRecComplete():
                wrsp = await self.judge_complete(player_input)
            case WRecObserve():
                wrsp = self.observe_at(player_input.position)
            case WRecMove():
                wrsp = self.move_player(player_input)
            case WRecInteract():
                wrsp = await self.route_interaction(player_input)
            case _:
                await asyncio.sleep(1)
                wrsp = WResError(
                    status=WResStatus.ERROR,
                    message=f"unknown request {player_input}",
                )
        return wrsp

    # ------------------------------------------------------------------
    # Entity management
    # ------------------------------------------------------------------

    def add_player(self, player: Player) -> None:
        """Register a player with the world."""
        self.players.append(player)

    def add_terrain(self, terrain: Terrain) -> None:
        """Add a terrain region to the world."""
        self.terrains.append(terrain)

    async def route_interaction(self, req: WRecInteract) -> WResInteract | WResError:
        """Route a message to the named target player and return its LLM reply.

        The target's receive_message coroutine must never touch world_input_queue;
        see Player.receive_message for the enforced contract.
        """
        target = next((p for p in self.players if p.name == req.target_name), None)
        if target is None:
            return WResError(
                status=WResStatus.ERROR,
                message=f"No player named {req.target_name!r} exists in the world.",
            )
        reply = await target.receive_message(
            sender_name=req.sender_name,
            sender_prompt=req.sender_prompt,
            message=req.message,
        )
        return WResInteract(
            status=WResStatus.SUCCESS,
            target_prompt=target.to_prompt(),
            reply=reply,
        )

    async def judge_and_build(self, req: WRecBuild) -> WResBuild:
        """Check collisions, then validate with the LLM judge, then add the building.

        The collision check runs first because it is free and the judge is a paid call.
        """
        collision = self.check_building_collision(req.building)
        if collision is not None:
            return collision
        result = await self.judge.check_build(
            building=req.building,
            observation=req.observation,
            player_state=req.player_state,
        )
        if not result.success:
            return WResBuild(status=WResStatus.ERROR, feedback=result.feedback)
        self.buildings.append(req.building)
        return WResBuild(status=WResStatus.SUCCESS, feedback=result.feedback)

    async def judge_craft(self, req: WRecCraft) -> WResCraft:
        """Validate a craft request with the LLM judge."""
        result = await self.judge.check_craft(
            utensil_name=req.utensil_name,
            description=req.description,
            observation=req.observation,
            player_state=req.player_state,
        )
        return WResCraft(
            status=WResStatus.from_bool(success=result.success),
            feedback=result.feedback,
        )

    async def judge_complete(self, req: WRecComplete) -> WResComplete:
        """Ask the LLM judge whether the reported outcome satisfies the objective."""
        result = await self.judge.check_complete(
            objective=req.objective,
            outcome=req.outcome,
            observation=req.observation,
            player_state=req.player_state,
        )
        alg.log(f"WR.judge_complete: {result.success} - {result.feedback}")
        return WResComplete(
            status=WResStatus.from_bool(success=result.success),
            feedback=result.feedback,
        )

    def check_building_collision(self, building: Building) -> WResBuild | None:
        """Return the error response if *building* collides with an existing one, else None."""
        for existing in self.buildings:
            if aabb_collides(building.position, building.size, existing.position, existing.size):
                return WResBuild(
                    status=WResStatus.ERROR,
                    feedback="Building collides with an existing building.",
                )
        return None

    def add_building(self, building: Building) -> WResBuild:
        """Add a building after checking for spatial collisions."""
        collision = self.check_building_collision(building)
        if collision is not None:
            return collision
        self.buildings.append(building)
        return WResBuild(status=WResStatus.SUCCESS, feedback="Building added.")

    def move_player(self, req: WRecMove) -> WResMoveStep:
        """Validate a one-step player move and return success or collision feedback.

        The player's position is NOT mutated here; the player updates itself
        after receiving SUCCESS.
        """
        player_size = req.player.size
        for building in self.buildings:
            if aabb_collides(req.new_position, player_size, building.position, building.size):
                return WResMoveStep(
                    status=WResStatus.ERROR,
                    obstacle=str(building),
                )
        for other in self.players:
            if other is req.player:
                continue
            if aabb_collides(req.new_position, player_size, other.position, other.size):
                return WResMoveStep(
                    status=WResStatus.ERROR,
                    obstacle=str(other),
                )
        return WResMoveStep(status=WResStatus.SUCCESS, new_position=req.new_position)

    def observe_at(self, position: Position, radius: int = 20) -> WResObserve:
        """Build a WorldMapObservation centred on *position* and return it."""
        nearby: list[NearbyEntity] = []

        for building in self.buildings:
            dist = euclidean(position, building.position)
            if dist <= radius:
                dx = building.position[0] - position[0]
                dy = building.position[1] - position[1]
                nearby.append(
                    NearbyEntity(
                        entity_type="building",
                        name=building.name,
                        relative_position=(dx, dy),
                        distance=dist,
                    )
                )

        for player in self.players:
            dist = euclidean(position, player.position)
            if dist == 0:
                # Skip the observing player (same tile)
                continue
            if dist <= radius:
                dx = player.position[0] - position[0]
                dy = player.position[1] - position[1]
                nearby.append(
                    NearbyEntity(
                        entity_type="player",
                        name=player.name,
                        relative_position=(dx, dy),
                        distance=dist,
                    )
                )

        for terrain in self.terrains:
            dist = euclidean(position, terrain.position)
            if dist <= radius:
                dx = terrain.position[0] - position[0]
                dy = terrain.position[1] - position[1]
                nearby.append(
                    NearbyEntity(
                        entity_type="terrain",
                        name=terrain.name,
                        relative_position=(dx, dy),
                        distance=dist,
                    )
                )

        obs = WorldMapObservation(
            player_position=position,
            nearby_entities=nearby,
            radius=radius,
        )
        return WResObserve(status=WResStatus.SUCCESS, observation=obs)
