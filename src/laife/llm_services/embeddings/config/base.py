"""Base class for LLM services embeddings configuration.

Provides a small, langchain-friendly config wrapper similar to the
chat `ChatConfig` implementation.
"""

from langchain.embeddings import Embeddings
from langchain.embeddings import init_embeddings

from laife.data_models.basemodel_kwargs import BaseModelKwargs


class EmbeddingsConfig(BaseModelKwargs):
    """Base config for an embeddings model usable with langchain's `init_embedding_model`.

    Fields should match the keywords expected by langchain's init function so
    `to_kw()` can be used directly.
    """

    model: str
    model_provider: str

    def create_embedding_model(self) -> Embeddings:
        """Instantiate the embeddings model from the config."""
        return init_embeddings(**self.to_kw(exclude_none=True))
