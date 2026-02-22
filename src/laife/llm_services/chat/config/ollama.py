"""Ollama chat configuration."""

from langchain_core.utils.utils import from_env
from pydantic import Field

from laife.llm_services.chat.config.base import ChatConfig


class OllamaChatConfig(ChatConfig):
    """Configuration for a locally-running Ollama chat model."""

    model: str = "llama3.2"
    """Ollama model tag to use."""
    model_provider: str = "ollama"
    """Provider name for init_chat_model."""
    base_url: str | None = Field(default_factory=from_env("OLLAMA_BASE_URL", default=None))
    """Ollama server URL. Reads OLLAMA_BASE_URL env var; defaults to None (langchain uses http://localhost:11434)."""
    max_tokens: int = 1024
    """Maximum number of tokens to generate."""
