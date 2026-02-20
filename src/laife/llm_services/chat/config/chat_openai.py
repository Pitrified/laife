"""Chat OpenAI configuration.

These are the default configuration settings for the OpenAI chat model.
"""

from langchain_core.utils.utils import secret_from_env
from pydantic import Field
from pydantic import SecretStr

from laife.llm_services.chat.config.base import ChatConfig


class ChatOpenAIConfig(ChatConfig):
    """Configuration for the OpenAI chat model."""

    model: str = "gpt-4o-mini"
    """Model name to use."""
    model_provider: str = "openai"
    """Provider name for init_chat_model."""
    api_key: SecretStr | None = Field(
        default_factory=secret_from_env("OPENAI_API_KEY", default=None)
    )
    """OpenAI API key. Reads OPENAI_API_KEY env var by default."""
