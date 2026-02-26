"""Params for search services."""

from laife.llm_services.vectorstores.config.base import VectorStoreConfig
from laife.llm_services.vectorstores.config.chroma import ChromaConfig
from laife.params.env_type import EnvType
from laife.params.llm_services.embeddings import EmbeddingsParams


class SearchParams:
    """Params for search services."""

    def __init__(
        self,
        env_type: EnvType,
        embeddings_params: EmbeddingsParams,
    ) -> None:
        """Load the params for search services."""
        self.env_type = env_type
        self.embeddings_params = embeddings_params
        self.load_params()

    def load_params(self) -> None:
        """Load the params for search services."""
        self.load_common_params_pre()

    def load_common_params_pre(self) -> None:
        """Load the common params."""
        self.chroma = ChromaConfig(
            embeddings_config=self.embeddings_params.default,
        )
        self.default: VectorStoreConfig = self.chroma

    def __str__(self) -> str:
        """Provide String representation of the SearchParams."""
        s = "SearchParams:"
        s += f"\n  ChromaConfig: {self.chroma}"
        return s

    def __repr__(self) -> str:
        """Provide String representation of the SearchParams."""
        return str(self)
