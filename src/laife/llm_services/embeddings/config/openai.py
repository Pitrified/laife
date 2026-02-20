"""Native OpenAI embeddings configuration."""

from langchain_core.utils.utils import secret_from_env
from pydantic import Field
from pydantic import SecretStr

from laife.llm_services.embeddings.config.base import EmbeddingsConfig


class OpenAIEmbeddingsConfig(EmbeddingsConfig):
    """Configuration for OpenAI embedding models."""

    model: str = "text-embedding-3-small"
    """Default OpenAI embedding model."""
    provider: str = "openai"
    """Provider name for init_embedding_model."""
    api_key: SecretStr | None = Field(
        default_factory=secret_from_env("OPENAI_API_KEY", default=None)
    )
    """OpenAI API key. Reads OPENAI_API_KEY env var by default."""
