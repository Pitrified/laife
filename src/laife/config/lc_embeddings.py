"""Config for langchain embedding models."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic.v1 import SecretStr

from laife.embed.utils import convert_to_secret_str


class OpenAIEmbeddingModelName(Enum):
    """Available OpenAI embedding model names."""

    text_embedding_3_small = "text-embedding-3-small"


class OpenAIEmbeddingsConfig:
    """Config for OpenAI embedding models."""

    def __init__(
        self,
        model_name: OpenAIEmbeddingModelName,
        api_key: str | SecretStr,
    ) -> None:
        """Initialize OpenAI embeddings configuration."""
        self.model_name = model_name
        self.api_key: SecretStr = convert_to_secret_str(api_key)

    def to_dict(self) -> dict[str, Any]:
        """Return the config as a plain dictionary."""
        return {
            "model": self.model_name.value,
            "api_key": self.api_key,
        }


class SentenceTransformerModelName(Enum):
    """Available SentenceTransformer model names."""

    mpnet = "sentence-transformers/all-mpnet-base-v2"


# TODO: this should basically be the same as the SentenceTransformersEmbeddings model
# class SentenceTransformersEmbeddings(BaseModel):
# with just the attrs that are needed for the config
# and some utils to post process the config


@dataclass
class SentenceTransformerConfig:
    """Config for SentenceTransformer embedding models."""

    model_name: SentenceTransformerModelName


LcEmbeddingsConfig = OpenAIEmbeddingsConfig | SentenceTransformerConfig
