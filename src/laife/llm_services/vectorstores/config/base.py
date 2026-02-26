"""Abstract base class for vector store configuration."""

from abc import ABC
from abc import abstractmethod

from langchain_core.vectorstores import VectorStore

from laife.data_models.basemodel_kwargs import BaseModelKwargs
from laife.llm_services.embeddings.config.base import EmbeddingsConfig


class VectorStoreConfig(BaseModelKwargs, ABC):
    """Abstract base config for a vector store.

    Subclasses must implement ``create_vector_store`` to return a live
    ``VectorStore`` instance backed by the provider of their choice.
    """

    collection_name: str = "laife"
    """Name of the collection inside the vector store."""
    embeddings_config: EmbeddingsConfig | None = None
    """Embeddings model config.  When provided it is forwarded to the store."""

    @abstractmethod
    def create_vector_store(self) -> VectorStore:
        """Instantiate and return a live vector store from this config."""
        ...
