"""WorldRunner - pure simulation loop, no pygame dependency."""

import asyncio

from laife.config.types import Position
from laife.entities.building import Building
from laife.entities.player import Player
from laife.entities.utils.geometry import aabb_collides
from laife.entities.world_channel import WRecBuild
from laife.entities.world_channel import WRecCraft
from laife.entities.world_channel import WRecInteract
from laife.entities.world_channel import WRecMove
from laife.entities.world_channel import WRecObserve
from laife.entities.world_channel import WReq
from laife.entities.world_channel import WRes
from laife.entities.world_channel import WResBuild
from laife.entities.world_channel import WResCraft
from laife.entities.world_channel import WResError
from laife.entities.world_channel import WResInteract
from laife.entities.world_channel import WResMoveStep
from laife.entities.world_channel import WResObserve
from laife.entities.world_channel import WResStatus
from laife.entities.world_judge import WorldActionJudge
from laife.entities.world_judge import WorldJudgeInput
from laife.entities.world_map_observation import NearbyEntity
from laife.entities.world_map_observation import WorldMapObservation
from laife.entities.world_map_observation import euclidean
from laife.llm.prompt_loader import PromptLoader
from laife.llm.prompt_loader import PromptLoaderConfig
from laife.params.laife_params import get_laife_params
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

        # LLM judges for build and craft actions
        laife_params = get_laife_params()
        build_prompt = PromptLoader(
            PromptLoaderConfig(
                base_prompt_fol=laife_params.paths.prompts_fol,
                prompt_name="world_judge_build",
            )
        ).load_prompt()
        craft_prompt = PromptLoader(
            PromptLoaderConfig(
                base_prompt_fol=laife_params.paths.prompts_fol,
                prompt_name="world_judge_craft",
            )
        ).load_prompt()
        self.build_judge = WorldActionJudge(
            chat_config=laife_params.llm_services.chat.default,
            prompt_str=build_prompt,
        )
        self.craft_judge = WorldActionJudge(
            chat_config=laife_params.llm_services.chat.default,
            prompt_str=craft_prompt,
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
        """Validate a build request with the LLM judge then add the building."""
        judge_input = WorldJudgeInput(
            action_type="build",
            action_details=(
                f"building_type={req.building.building_type.building_type}"
                f", name={req.building.name}"
                f", size={req.building.size}"
                f", description={req.building.description}"
            ),
            observation=req.observation,
            player_state=req.player_state,
        )
        result = await self.build_judge.ainvoke(judge_input)
        if not result.success:
            return WResBuild(status=WResStatus.ERROR, feedback=result.feedback)
        # Judge approved - fall through to spatial check
        spatial_res = self.add_building(req.building)
        if spatial_res.status == WResStatus.ERROR:
            return spatial_res
        return WResBuild(status=WResStatus.SUCCESS, feedback=result.feedback)

    async def judge_craft(self, req: WRecCraft) -> WResCraft:
        """Validate a craft request with the LLM judge."""
        judge_input = WorldJudgeInput(
            action_type="craft",
            action_details=(f"utensil_name={req.utensil_name}, description={req.description}"),
            observation=req.observation,
            player_state=req.player_state,
        )
        result = await self.craft_judge.ainvoke(judge_input)
        return WResCraft(
            status=WResStatus.from_bool(success=result.success),
            feedback=result.feedback,
        )

    def add_building(self, building: Building) -> WResBuild:
        """Add a building after checking for spatial collisions."""
        for existing in self.buildings:
            if aabb_collides(building.position, building.size, existing.position, existing.size):
                return WResBuild(
                    status=WResStatus.ERROR,
                    feedback="Building collides with an existing building.",
                )
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

        obs = WorldMapObservation(
            player_position=position,
            nearby_entities=nearby,
            radius=radius,
        )
        return WResObserve(status=WResStatus.SUCCESS, observation=obs)
