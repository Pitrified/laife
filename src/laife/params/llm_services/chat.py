"""Params for chat services."""

from typing import TYPE_CHECKING

from laife.llm_services.chat.config.azure_openai import AzureOpenAIChatConfig
from laife.llm_services.chat.config.chat_openai import ChatOpenAIConfig
from laife.params.env_type import EnvType

if TYPE_CHECKING:
    from laife.llm_services.chat.config.base import ChatConfig


class ChatParams:
    """Params for chat services.

    Holds one or more ChatConfig instances.
    Swap out ``default`` for a different provider config as needed.
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
        self.default: ChatConfig = ChatOpenAIConfig()

        self.azure = AzureOpenAIChatConfig(
            temperature=1,
            model="gpt-5.2-chat",
        )

    def __str__(self) -> str:
        """Provide String representation of the ChatParams."""
        return f"ChatParams: default={self.default.model_provider}/{self.default.model}"

    def __repr__(self) -> str:
        """Provide String representation of the ChatParams."""
        return str(self)
