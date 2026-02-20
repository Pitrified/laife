"""Azure OpenAI chat configuration."""

from langchain_core.utils.utils import from_env
from langchain_core.utils.utils import secret_from_env
from pydantic import Field
from pydantic import SecretStr

from laife.llm_services.chat.config.base import ChatConfig


class AzureOpenAIChatConfig(ChatConfig):
    """Configuration for the Azure OpenAI chat model."""

    model: str = "gpt-4o-mini"
    """Azure deployment model name."""
    model_provider: str = "azure_openai"
    """Provider name for init_chat_model."""
    api_key: SecretStr | None = Field(
        default_factory=secret_from_env("AZURE_OPENAI_API_KEY", default=None)
    )
    """Azure OpenAI API key. Reads AZURE_OPENAI_API_KEY env var by default."""
    azure_endpoint: str | None = Field(
        default_factory=from_env("AZURE_OPENAI_ENDPOINT", default=None)
    )
    """Azure OpenAI endpoint. Reads AZURE_OPENAI_ENDPOINT env var by default."""
    api_version: str = "2024-02-01"
    """Azure OpenAI API version."""
