"""Params for embedding services."""

from typing import TYPE_CHECKING

from llm_core.embeddings.config.openai import OpenAIEmbeddingsConfig

if TYPE_CHECKING:
    from llm_core.embeddings.config.base import EmbeddingsConfig

    from laife.params.env_type import EnvType


class EmbeddingsParams:
    """Params for embedding services.

    Holds the OpenAI EmbeddingsConfig; callers read ``default``.
    """

    def __init__(self, env_type: EnvType) -> None:
        """Load the params for embedding services."""
        self.env_type = env_type
        self.load_params()

    def load_params(self) -> None:
        """Load the params for embedding services."""
        self.openai = OpenAIEmbeddingsConfig()
        self.default: EmbeddingsConfig = self.openai

    def __str__(self) -> str:
        """Provide String representation of the EmbeddingsParams."""
        return f"EmbeddingsParams: default={self.default.provider}/{self.default.model}"

    def __repr__(self) -> str:
        """Provide String representation of the EmbeddingsParams."""
        return str(self)
