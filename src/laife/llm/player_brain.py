"""Brain of a player."""

import time

from pydantic import BaseModel

from laife.entities.action import ActionPicker
from laife.entities.action import ActionPickerInput
from laife.entities.action import BaseAction
from laife.entities.world_map_observation import WorldMapObservation
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.llm.prompt_loader import PromptLoader
from laife.llm.prompt_loader import PromptLoaderConfig
from laife.llm_services.chat.config.base import ChatConfig
from laife.meta.log_events import EVT_LLM_CALL
from laife.meta.logger import slog


class PlayerBrainConfig(BaseModel):
    """Configuration for the PlayerBrain."""

    chat_config: ChatConfig
    prompt_loader_config: PromptLoaderConfig


class PlayerBrain:
    """Brain of a player.

    Instantiate with a :class:`PlayerBrainConfig`. Owns the :class:`ActionPicker`
    chain; calling :meth:`think` returns a concrete :class:`BaseAction`.
    """

    def __init__(self, config: PlayerBrainConfig) -> None:
        """Initialise the brain from config."""
        self.config = config
        self.prompt_str = PromptLoader(config.prompt_loader_config).load_prompt()
        self.action_picker = ActionPicker(
            chat_config=config.chat_config,
            prompt_str=self.prompt_str,
        )

    async def think(
        self,
        mission: Mission,
        history: MissionHistory,
        observation: WorldMapObservation,
        player_state: str,
        inventory: str,
    ) -> BaseAction:
        """Ask the LLM to pick the next action given full context."""
        t0 = time.monotonic()
        result = await self.action_picker.ainvoke(
            ActionPickerInput(
                mission=mission.to_prompt(),
                history=history.to_prompt(),
                observation=observation.to_prompt(),
                player_state=player_state,
                inventory=inventory,
            )
        )
        slog.bind(
            event=EVT_LLM_CALL,
            model=self.config.chat_config.model,
            elapsed=round(time.monotonic() - t0, 3),
        ).info(EVT_LLM_CALL)
        return result
