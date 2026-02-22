"""Params for embedding services."""

from typing import TYPE_CHECKING

from laife.llm_services.embeddings.config.azure_openai import AzureOpenAIEmbeddingsConfig
from laife.llm_services.embeddings.config.huggingface import HuggingFaceEmbeddingsConfig
from laife.llm_services.embeddings.config.ollama import OllamaEmbeddingsConfig
from laife.llm_services.embeddings.config.openai import OpenAIEmbeddingsConfig
from laife.params.env_type import EnvType

if TYPE_CHECKING:
    from laife.llm_services.embeddings.config.base import EmbeddingsConfig


class EmbeddingsParams:
    """Params for embedding services.

    Holds one or more EmbeddingsConfig instances.
    Swap ``default`` for a different provider config as needed.
    """

    def __init__(self, env_type: EnvType) -> None:
        """Load the params for embedding services."""
        self.env_type = env_type
        self.load_params()

    def load_params(self) -> None:
        """Load the params for embedding services."""
        self.openai = OpenAIEmbeddingsConfig()
        self.azure = AzureOpenAIEmbeddingsConfig()
        self.huggingface = HuggingFaceEmbeddingsConfig()
        self.ollama = OllamaEmbeddingsConfig()
        self.default: EmbeddingsConfig = self.openai

    def __str__(self) -> str:
        """Provide String representation of the EmbeddingsParams."""
        return f"EmbeddingsParams: default={self.default.provider}/{self.default.model}"

    def __repr__(self) -> str:
        """Provide String representation of the EmbeddingsParams."""
        return str(self)
