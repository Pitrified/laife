"""Params for chat services."""

from typing import TYPE_CHECKING

from llm_core.chat.config.openai import ChatOpenAIConfig

if TYPE_CHECKING:
    from llm_core.chat.config.base import ChatConfig

    from laife.params.env_type import EnvType


class ChatParams:
    """Params for chat services.

    Holds the OpenAI ChatConfig; callers read ``default``.
    """

    def __init__(
        self,
        env_type: EnvType,
    ) -> None:
        """Load the params for chat services."""
        self.env_type = env_type
        self.load_params()

    def load_params(self) -> None:
        """Load the params for chat services."""
        # luna only accepts temperature 1 unless reasoning_effort is "none".
        self.openai = ChatOpenAIConfig(
            temperature=1,
            model="gpt-6-luna",
        )

        self.default: ChatConfig = self.openai

    def __str__(self) -> str:
        """Provide String representation of the ChatParams."""
        return f"ChatParams: default={self.default.model_provider}/{self.default.model}"

    def __repr__(self) -> str:
        """Provide String representation of the ChatParams."""
        return str(self)
