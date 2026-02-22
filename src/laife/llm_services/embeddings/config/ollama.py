"""Ollama embeddings configuration."""

from langchain_core.utils.utils import from_env
from pydantic import Field

from laife.llm_services.embeddings.config.base import EmbeddingsConfig


class OllamaEmbeddingsConfig(EmbeddingsConfig):
    """Configuration for a locally-running Ollama embedding model."""

    model: str = "nomic-embed-text"
    """Ollama embedding model tag to use."""
    provider: str = "ollama"
    """Provider name for init_embeddings."""
    base_url: str | None = Field(default_factory=from_env("OLLAMA_BASE_URL", default=None))
    """Ollama server URL. Reads OLLAMA_BASE_URL env var; defaults to None (langchain uses http://localhost:11434)."""
