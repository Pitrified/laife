"""Base class for LLM services embeddings configuration.

Leverage `init_embeddings`:
https://reference.langchain.com/python/langchain/embeddings/base/init_embeddings
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
    provider: str

    def create_embedding_model(self) -> Embeddings:
        """Instantiate the embeddings model from the config."""
        return init_embeddings(**self.to_kw(exclude_none=True))
