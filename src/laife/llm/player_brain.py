"""Brain of a player."""

from typing import TYPE_CHECKING

from llm_core.chains.structured_chain import StructuredLLMChain
from llm_core.chat.config.base import ChatConfig
from llm_core.prompts.prompt_loader import PromptLoader
from llm_core.prompts.prompt_loader import PromptLoaderConfig
from pydantic import BaseModel

from laife.entities.action import ActionEnvelope
from laife.entities.action import ActionPickerInput
from laife.entities.action import BaseAction
from laife.llm.mission_generator import MissionGeneratorInput
from laife.llm.mission_generator import MissionGeneratorResult
from laife.llm.player_planner import PlayerPlannerInput
from laife.llm.player_planner import PlayerPlannerResult
from laife.llm.player_replier import PlayerReplyInput
from laife.llm.player_replier import PlayerReplyOutput
from laife.meta.logger import timed_llm_call

if TYPE_CHECKING:
    from contextlib import AbstractContextManager

    from laife.entities.world_map_observation import WorldMapObservation
    from laife.llm.mission import Mission
    from laife.llm.mission import MissionHistory


class PlayerBrainConfig(BaseModel):
    """Configuration for the PlayerBrain: one chat config, one prompt per chain."""

    chat_config: ChatConfig
    action_prompt: PromptLoaderConfig
    plan_prompt: PromptLoaderConfig
    reply_prompt: PromptLoaderConfig
    mission_prompt: PromptLoaderConfig


class PlayerBrain:
    """The thinking of one player: owns the player's four LLM chains.

    Each method takes plain values, times its one LLM call and returns the
    parsed result; applying it to the player is the caller's job. The brain
    holds no world queue, so nothing it does can reach the world: the world
    calls :meth:`reply` from inside its own loop, where a world request would
    deadlock.
    """

    def __init__(self, config: PlayerBrainConfig, player_name: str) -> None:
        """Build the four chains from config; *player_name* labels the timing records."""
        self.config = config
        self.player_name = player_name
        self.action_chain = StructuredLLMChain(
            chat_config=config.chat_config,
            prompt_str=PromptLoader(config.action_prompt).load_prompt(),
            input_model=ActionPickerInput,
            output_model=ActionEnvelope,
        )
        self.plan_chain = StructuredLLMChain(
            chat_config=config.chat_config,
            prompt_str=PromptLoader(config.plan_prompt).load_prompt(),
            input_model=PlayerPlannerInput,
            output_model=PlayerPlannerResult,
        )
        self.reply_chain = StructuredLLMChain(
            chat_config=config.chat_config,
            prompt_str=PromptLoader(config.reply_prompt).load_prompt(),
            input_model=PlayerReplyInput,
            output_model=PlayerReplyOutput,
        )
        self.mission_chain = StructuredLLMChain(
            chat_config=config.chat_config,
            prompt_str=PromptLoader(config.mission_prompt).load_prompt(),
            input_model=MissionGeneratorInput,
            output_model=MissionGeneratorResult,
        )

    def _timed(self, stage: str, turn: int) -> AbstractContextManager[None]:
        """Time one LLM call of this brain under *stage*."""
        return timed_llm_call(
            player=self.player_name,
            turn=turn,
            model=self.config.chat_config.model,
            stage=stage,
        )

    async def next_action(
        self,
        mission: Mission,
        history: MissionHistory,
        observation: WorldMapObservation,
        player_state: str,
        inventory: str,
        turn: int,
    ) -> BaseAction:
        """Pick the next action for *mission*."""
        with self._timed("action", turn):
            envelope = await self.action_chain.ainvoke(
                ActionPickerInput(
                    mission=mission.to_prompt(),
                    history=history.to_prompt(),
                    observation=observation.to_prompt(),
                    player_state=player_state,
                    inventory=inventory,
                    nearby_players=observation.nearby_players_to_prompt(),
                )
            )
        return envelope.act

    async def plan(
        self,
        mission: Mission,
        history: MissionHistory,
        observation: WorldMapObservation,
        player_state: str,
        turn: int,
    ) -> PlayerPlannerResult:
        """Decompose *mission* into ordered sub-mission objectives."""
        with self._timed("plan", turn):
            return await self.plan_chain.ainvoke(
                PlayerPlannerInput(
                    mission=mission.to_prompt(),
                    history=history.to_prompt(),
                    observation=observation.to_prompt(),
                    player_state=player_state,
                )
            )

    async def propose_mission(
        self,
        observation: WorldMapObservation,
        player_state: str,
        inventory: str,
        turn: int,
    ) -> MissionGeneratorResult:
        """Propose a mission objective for the current situation."""
        with self._timed("mission", turn):
            return await self.mission_chain.ainvoke(
                MissionGeneratorInput(
                    observation=observation.to_prompt(),
                    player_state=player_state,
                    inventory=inventory,
                )
            )

    async def reply(
        self,
        sender_name: str,
        sender_prompt: str,
        message: str,
        player_state: str,
        mission: Mission,
        history: MissionHistory,
        turn: int,
    ) -> str:
        """Write an in-character reply to *message* from *sender_name*."""
        with self._timed("reply", turn):
            result = await self.reply_chain.ainvoke(
                PlayerReplyInput(
                    sender_name=sender_name,
                    sender_prompt=sender_prompt,
                    message=message,
                    own_state=player_state,
                    own_mission=mission.to_prompt(),
                    own_history=history.to_prompt(),
                )
            )
        return result.reply
