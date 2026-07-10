"""Brain of a player."""

from llm_core.chat.config.base import ChatConfig
from llm_core.prompts.prompt_loader import PromptLoader
from llm_core.prompts.prompt_loader import PromptLoaderConfig
from pydantic import BaseModel

from laife.entities.action import ActionPicker
from laife.entities.action import ActionPickerInput
from laife.entities.action import BaseAction
from laife.entities.world_map_observation import WorldMapObservation
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.meta.logger import timed_llm_call


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
        player: str = "",
        turn: int = -1,
    ) -> BaseAction:
        """Ask the LLM to pick the next action given full context."""
        with timed_llm_call(
            player=player,
            turn=turn,
            model=self.config.chat_config.model,
            stage="action",
        ):
            result = await self.action_picker.ainvoke(
                ActionPickerInput(
                    mission=mission.to_prompt(),
                    history=history.to_prompt(),
                    observation=observation.to_prompt(),
                    player_state=player_state,
                    inventory=inventory,
                )
            )
        return result
