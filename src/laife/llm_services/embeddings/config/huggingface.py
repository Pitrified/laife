"""HuggingFace / SentenceTransformer embeddings configuration."""

from laife.llm_services.embeddings.config.base import EmbeddingsConfig


class HuggingFaceEmbeddingsConfig(EmbeddingsConfig):
    """Configuration for HuggingFace / SentenceTransformer embedding models."""

    model: str = "sentence-transformers/all-mpnet-base-v2"
    """Default SentenceTransformer model."""
    model_provider: str = "huggingface"
    """Provider name for init_embeddings."""
