"""Brain of a player."""

from pydantic import BaseModel

from laife.llm.prompt_loader import PromptLoader
from laife.llm.prompt_loader import PromptLoaderConfig
from laife.llm_services.chat.config.base import ChatConfig


class PlayerBrainConfig(BaseModel):
    """Configuration for the PlayerBrain."""

    chat_config: ChatConfig
    prompt_loader_config: PromptLoaderConfig


class PlayerBrain:
    """Brain of a player.

    Instantiate with a :class:`PlayerBrainConfig`. The brain handles interaction
    with the language model; action-picking wiring is added in Phase 4/5.
    """

    def __init__(self, config: PlayerBrainConfig) -> None:
        """Initialise the brain from config."""
        self.config = config
        self.llm = config.chat_config.create_chat_model()
        self.prompt_str = PromptLoader(config.prompt_loader_config).load_prompt()

    async def think(self, query: str) -> str:
        """Stub — will be replaced in Phase 5 with full action-returning signature."""
        raise NotImplementedError("think() will be wired in Phase 5")
