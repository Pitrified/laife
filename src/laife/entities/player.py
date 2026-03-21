"""Player entity - agent logic and state, no pygame dependency."""

import asyncio
from enum import StrEnum
import time

from llm_core.prompts.prompt_loader import PromptLoaderConfig

from laife.config.types import Position
from laife.config.types import Size
from laife.entities.action import ActionBuild
from laife.entities.action import ActionComplete
from laife.entities.action import ActionCraft
from laife.entities.action import ActionInteract
from laife.entities.action import ActionMove
from laife.entities.action import ActionPlan
from laife.entities.action import BaseAction
from laife.entities.building import Building
from laife.entities.building import BuildingType
from laife.entities.utensil import Utensil
from laife.entities.utils.directions import cardinal_to_delta
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
from laife.entities.world_channel import WResMove
from laife.entities.world_channel import WResMoveStep
from laife.entities.world_channel import WResObserve
from laife.entities.world_channel import WResPlan
from laife.entities.world_channel import WResStatus
from laife.entities.world_map_observation import WorldMapObservation
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionHistoryEntry
from laife.llm.mission import MissionStatus
from laife.llm.mission_generator import MissionGenerator
from laife.llm.mission_generator import MissionGeneratorConfig
from laife.llm.player_brain import PlayerBrain
from laife.llm.player_brain import PlayerBrainConfig
from laife.llm.player_planner import PlayerPlanner
from laife.llm.player_planner import PlayerPlannerConfig
from laife.llm.player_replier import PlayerReplier
from laife.llm.player_replier import PlayerReplierConfig
from laife.llm.player_replier import PlayerReplyInput
from laife.meta.log_events import EVT_ACTION
from laife.meta.log_events import EVT_MISSION_TRANSITION
from laife.meta.log_events import EVT_WORLD_RESPONSE
from laife.meta.logger import slog
from laife.params.laife_params import get_laife_params
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
        size: Size = (1, 1),
    ) -> None:
        """Create the player.

        The play loop is NOT started here.  The caller is responsible for
        starting it (e.g. via asyncio.create_task or asyncio.gather).
        """
        self.name: str = name
        self.player_type: str = player_type
        self.size: Size = size

        # logical state - no sprite side-effects
        self.position: Position = position
        self.state: PlayerState = state

        # communication channels
        self.world_input_queue: asyncio.Queue[WReq] = world_input_queue
        self.input_queue: asyncio.Queue[WRes] = asyncio.Queue()

        # observation, will be stale for a tick
        self.last_observation: WorldMapObservation = WorldMapObservation.from_position(position)

        # cognition
        laife_params = get_laife_params()
        self.brain = PlayerBrain(
            PlayerBrainConfig(
                chat_config=laife_params.llm_services.chat.default,
                prompt_loader_config=PromptLoaderConfig(
                    base_prompt_fol=laife_params.paths.prompts_fol,
                    prompt_name="player_brain",
                ),
            )
        )
        self.planner = PlayerPlanner(
            PlayerPlannerConfig(
                chat_config=laife_params.llm_services.chat.default,
                prompt_loader_config=PromptLoaderConfig(
                    base_prompt_fol=laife_params.paths.prompts_fol,
                    prompt_name="player_planner",
                ),
            )
        )
        self.replier = PlayerReplier(
            PlayerReplierConfig(
                chat_config=laife_params.llm_services.chat.default,
                prompt_loader_config=PromptLoaderConfig(
                    base_prompt_fol=laife_params.paths.prompts_fol,
                    prompt_name="player_reply",
                ),
            )
        )
        self.mission_generator = MissionGenerator(
            MissionGeneratorConfig(
                chat_config=laife_params.llm_services.chat.default,
                prompt_loader_config=PromptLoaderConfig(
                    base_prompt_fol=laife_params.paths.prompts_fol,
                    prompt_name="mission_generator",
                ),
            )
        )
        # Mission starts PENDING; the first play() iteration will generate a real objective.
        self.mission = Mission(
            objective="",
            status=MissionStatus.PENDING,
        )
        self.history = MissionHistory()
        self.inventory: list[Utensil] = []

    def render_state(self) -> str:
        """Return a string representation of the player's state for rendering."""
        return f"{self.name} at {self.position} - {self.state}"

    def to_prompt(self) -> str:
        """Return a concise snapshot of this player for use in LLM prompts."""
        return (
            f"Name: {self.name}\n"
            f"Type: {self.player_type}\n"
            f"Position: {self.position}\n"
            f"Mission: {self.mission.to_prompt()}"
        )

    def inventory_to_prompt(self) -> str:
        """Return a human-readable inventory listing for use in LLM prompts."""
        if not self.inventory:
            return "Empty - no utensils carried."
        return "\n".join(f"- {u.to_prompt()}" for u in self.inventory)

    # ------------------------------------------------------------------
    # Agent loop
    # ------------------------------------------------------------------

    async def play(self) -> None:
        """Run the agent decision loop (intended to run as an asyncio task)."""
        while True:
            # Refresh observation before deciding
            await self.observe()
            # Generate a mission if none is active yet or the previous one finished.
            if self.mission.status == MissionStatus.PENDING or self.mission.is_terminal():
                new_obj = await self._generate_mission_objective()
                self._start_new_mission(new_obj)
            alg.log(f"PLAYER.play {self.name}: needs to {self.mission}")
            # Think on how to solve the mission
            action = await self.think(focus=self.mission.active_focus())
            match action:
                case ActionMove() as act:
                    wrsp = await self.move(act)
                case ActionBuild() as act:
                    wrsp = await self.build(act)
                case ActionCraft() as act:
                    wrsp = await self.craft(act)
                case ActionPlan() as act:
                    wrsp = await self.plan(act)
                case ActionComplete() as act:
                    wrsp = await self.complete(act)
                case ActionInteract() as act:
                    wrsp = await self.interact(act)
                case _:
                    wrsp = await self.action_error(action)
            he = MissionHistoryEntry(action=action, result=str(wrsp))
            self.history.add_history_entry(he)
            self._update_mission_from_response(action, wrsp)

    # ------------------------------------------------------------------
    # Mission lifecycle helpers
    # ------------------------------------------------------------------

    def _update_mission_from_response(self, action: BaseAction, wrsp: WRes) -> None:
        """Update mission status based on the world response to a build or craft action.

        Only ``ActionBuild`` and ``ActionCraft`` responses drive mission status
        transitions - move, plan, and interact responses are neutral.
        """
        if (isinstance(action, ActionBuild) and isinstance(wrsp, WResBuild)) or (
            isinstance(action, ActionCraft) and isinstance(wrsp, WResCraft)
        ):
            if wrsp.status == WResStatus.SUCCESS:
                self.mission.record_action_success()
            else:
                self.mission.record_action_failure()
            slog.bind(
                event=EVT_MISSION_TRANSITION,
                player=self.name,
                to_status=self.mission.status.value,
            ).info(EVT_MISSION_TRANSITION)

    def _start_new_mission(self, objective: str) -> None:
        """Transition to a fresh ACTIVE mission with the given objective.

        Resets the mission history.  The *objective* string should come from
        :meth:`_generate_mission_objective` so that goals are LLM-driven rather
        than hardcoded.
        """
        old_status = self.mission.status
        alg.log(
            f"PLAYER {self.name}: mission '{self.mission.objective}' ended"
            f" with status {old_status.value} - starting new mission: '{objective}'"
        )
        self.mission = Mission(
            objective=objective,
            status=MissionStatus.ACTIVE,
        )
        self.history = MissionHistory()

    async def _generate_mission_objective(self) -> str:
        """Ask the mission-generator LLM to propose an objective for the current situation.

        Uses the cached observation so no extra world round-trip is needed.
        """
        alg.log(f"PLAYER {self.name}: generating new mission objective")
        result = await self.mission_generator.ainvoke(
            observation=self.last_observation,
            player_state=self.render_state(),
            inventory=self.inventory_to_prompt(),
        )
        alg.log(f"PLAYER {self.name}: proposed mission '{result.objective}' - {result.reason}")
        return result.objective

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    async def think(self, focus: Mission | None = None) -> BaseAction:
        """Decide what to do next by calling the LLM brain.

        If *focus* is given the brain reasons about that sub-mission instead
        of the top-level mission, keeping the LLM context tight.
        """
        self.state = PlayerState.THINKING
        target = focus if focus is not None else self.mission
        alg.log(f"{self.name} is thinking about '{target.objective}'")
        action = await self.brain.think(
            mission=target,
            history=self.history,
            observation=self.last_observation,
            player_state=self.render_state(),
            inventory=self.inventory_to_prompt(),
        )
        alg.log(f"PLAYER.play {self.name}: picked {action}")
        slog.bind(event=EVT_ACTION, player=self.name, action=str(action)).info(EVT_ACTION)
        self.state = PlayerState.IDLE
        return action

    async def _world_request[T: WRes](self, wreq: WReq, response_type: type[T]) -> T:
        """Send *wreq* to the world, assert the response type, and return it.

        Raises ``TypeError`` if the world returns an unexpected response type.
        The world channel is expected to be reliable; a type mismatch signals
        a world implementation bug and should fail loudly.
        """
        await self.world_input_queue.put(wreq)
        wrsp = await self.input_queue.get()
        self.input_queue.task_done()
        if not isinstance(wrsp, response_type):
            msg = f"Expected {response_type.__name__}, got {type(wrsp).__name__}"
            raise TypeError(msg)
        return wrsp

    async def observe(self) -> WResObserve:
        """Request a world observation and cache it in last_observation."""
        alg.log(f"PLAYER.observe {self.name}: requesting observation")
        wreq = WRecObserve(position=self.position, response_queue=self.input_queue)
        wrsp = await self._world_request(wreq, WResObserve)
        self.last_observation = wrsp.observation
        alg.log(
            f"PLAYER.observe {self.name}:"
            f" got observation at {self.last_observation.player_position}"
        )
        return wrsp

    async def plan(self, action: ActionPlan) -> WResPlan:
        """Decompose the current mission into sub-missions using the planner LLM."""
        alg.log(f"PLAYER.plan {self.name}: planning for '{action.reason}'")
        self.state = PlayerState.THINKING
        result = await self.planner.ainvoke(
            mission=self.mission,
            history=self.history,
            observation=self.last_observation,
            player_state=self.render_state(),
        )
        for sub_objective in result.sub_missions:
            self.mission.add_sub_mission(sub_objective)
        self.mission.advance()  # activate the first pending step immediately
        self.history = MissionHistory()
        alg.log(
            f"PLAYER.plan {self.name}: created {len(result.sub_missions)} sub-mission(s):"
            f" {result.sub_missions}"
        )
        self.state = PlayerState.IDLE
        return WResPlan(
            status=WResStatus.SUCCESS,
            sub_missions=result.sub_missions,
            reason=result.reason,
        )

    async def complete(self, action: ActionComplete) -> WResComplete:
        """Ask the world to verify completion; advance only on SUCCESS."""
        focus = self.mission.active_focus()
        alg.log(f"PLAYER.complete {self.name}: requesting world verdict for '{focus.objective}'")
        wreq = WRecComplete(
            objective=focus.objective,
            outcome=action.outcome,
            observation=self.last_observation.to_prompt(),
            player_state=self.render_state(),
            response_queue=self.input_queue,
        )
        wrsp = await self._world_request(wreq, WResComplete)

        if wrsp.status == WResStatus.ERROR:
            # World rejected the claim - mission stays ACTIVE, brain will retry
            alg.log(f"PLAYER.complete {self.name}: world rejected - {wrsp.feedback}")
            return wrsp

        focus.status = MissionStatus.COMPLETED
        advanced = self.mission.advance()
        self.history = MissionHistory()  # fresh slate for the new focus
        next_label = self.mission.active_focus().objective if advanced else "all steps done"
        msg = f"Completed '{focus.objective}'. Next: '{next_label}'."
        alg.log(f"PLAYER.complete {self.name}: {msg}")
        return WResComplete(
            status=WResStatus.SUCCESS,
            feedback="",
            message=msg,
            outcome=action.outcome,
        )

    async def move(self, action: ActionMove) -> WResMove:
        """Move the player in delta steps, each validated by the world."""
        self.state = PlayerState.MOVING
        start_position = self.position
        dx, dy = cardinal_to_delta(action.direction)
        alg.log(f"PLAYER.move {self.name}: moving {action.direction.value} x{action.distance}")

        for step in range(action.distance):
            new_pos = (self.position[0] + dx, self.position[1] + dy)
            wreq = WRecMove(
                player=self,
                new_position=new_pos,
                response_queue=self.input_queue,
            )
            wrsp_step = await self._world_request(wreq, WResMoveStep)

            if wrsp_step.status == WResStatus.ERROR:
                alg.log(f"PLAYER.move {self.name}: blocked at step {step}")
                self.state = PlayerState.IDLE
                return WResMove(
                    status=WResStatus.ERROR,
                    message=(
                        f"Blocked after {step} step(s) from {start_position}. "
                        f"Obstacle: {wrsp_step.obstacle or 'unknown'}."
                    ),
                )

            # World validated the step - player owns its position update
            self.position = new_pos

        alg.log(f"PLAYER.move {self.name}: moved to {self.position}")
        self.state = PlayerState.IDLE
        return WResMove(status=WResStatus.SUCCESS, message=f"Moved {action.distance} step(s).")

    def move_delta(self, dx: int, dy: int) -> None:
        """Adjust the player's position by delta values."""
        self.position = (self.position[0] + dx, self.position[1] + dy)

    async def build(self, action: ActionBuild) -> WResBuild:
        """Prepare and send a build request to the world."""
        alg.log(f"PLAYER.build {self.name}: building {action.building_type}")
        building = Building(
            name=action.building_type,
            building_type=BuildingType(
                building_type=action.building_type,
                description=action.description,
                size=(action.size, action.size),
            ),
            position=self.position,
            description=action.description,
        )
        wreq = WRecBuild(
            building=building,
            observation=self.last_observation.to_prompt(),
            player_state=self.render_state(),
            response_queue=self.input_queue,
        )
        wrsp = await self._world_request(wreq, WResBuild)
        alg.log(f"PLAYER.build {self.name}: got response {wrsp}")
        slog.bind(
            event=EVT_WORLD_RESPONSE,
            player=self.name,
            kind="build",
            status=wrsp.status.value,
        ).info(EVT_WORLD_RESPONSE)
        return wrsp

    async def craft(self, action: ActionCraft) -> WResCraft:
        """Prepare and send a craft request to the world."""
        alg.log(f"PLAYER.craft {self.name}: crafting {action.utensil_name}")
        wreq = WRecCraft(
            utensil_name=action.utensil_name,
            description=action.description,
            observation=self.last_observation.to_prompt(),
            player_state=self.render_state(),
            response_queue=self.input_queue,
        )
        wrsp = await self._world_request(wreq, WResCraft)
        if wrsp.status == WResStatus.SUCCESS:
            utensil = Utensil(name=action.utensil_name, description=action.description)
            self.inventory.append(utensil)
            alg.log(f"PLAYER.craft {self.name}: added {utensil.name} to inventory")
        alg.log(f"PLAYER.craft {self.name}: got response {wrsp}")
        slog.bind(
            event=EVT_WORLD_RESPONSE,
            player=self.name,
            kind="craft",
            status=wrsp.status.value,
        ).info(EVT_WORLD_RESPONSE)
        return wrsp

    async def action_error(self, action: BaseAction) -> WResError:
        """Handle an unknown action type."""
        alg.log(f"PLAYER.play {self.name}: unknown action {action}")
        await asyncio.sleep(1)
        return WResError(status=WResStatus.ERROR, message=f"unknown action {action}")

    async def receive_message(
        self,
        sender_name: str,
        sender_prompt: str,
        message: str,
    ) -> str:
        """Generate an in-character reply to a message from another player.

        This method must never put anything onto world_input_queue.
        It is called directly by WorldRunner inside handle_player_input and
        must remain free of all world I/O - only the external LLM call is
        awaited.
        """
        result = await self.replier.ainvoke(
            PlayerReplyInput(
                sender_name=sender_name,
                sender_prompt=sender_prompt,
                message=message,
                own_state=self.render_state(),
                own_mission=self.mission.to_prompt(),
                own_history=self.history.to_prompt(),
            )
        )
        return result.reply

    async def interact(self, action: ActionInteract) -> WResInteract:
        """Send a natural-language message to a nearby player and await the reply."""
        alg.log(f"PLAYER.interact {self.name}: messaging {action.target_name!r}")
        wreq = WRecInteract(
            sender_name=self.name,
            sender_prompt=self.to_prompt(),
            target_name=action.target_name,
            message=action.message,
            response_queue=self.input_queue,
        )
        wrsp = await self._world_request(wreq, WResInteract)
        alg.log(f"PLAYER.interact {self.name}: got reply {wrsp!r}")
        return wrsp

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
