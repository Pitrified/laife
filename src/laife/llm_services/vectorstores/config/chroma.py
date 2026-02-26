"""Chroma vector store configuration."""

from laife.llm_services.vectorstores.cchroma import CChroma
from laife.llm_services.vectorstores.config.base import VectorStoreConfig


class ChromaConfig(VectorStoreConfig):
    """Config for a local or server-backed Chroma vector store.

    Three deployment modes are supported — pick the fields that apply:

    * **In-memory / ephemeral** — leave all optional fields as ``None``.
    * **Local persistent** — set ``persist_directory``.
    * **Remote server** — set ``host`` and optionally ``port`` / ``ssl``.
    """

    # local persistent store ------------------------------------------------
    persist_directory: str | None = None
    """Filesystem path for a persistent local Chroma store."""

    # remote / server --------------------------------------------------------
    host: str | None = None
    """Hostname of a deployed Chroma server."""
    port: int | None = None
    """Port of a deployed Chroma server (Chroma default: 8000)."""
    ssl: bool = False
    """Whether to use SSL when connecting to a remote Chroma server."""

    def create_vector_store(self) -> CChroma:
        """Return a ``CChroma`` instance constructed from this config."""
        return CChroma(
            embeddings_config=self.embeddings_config,
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            host=self.host,
            port=self.port,
            ssl=self.ssl,
        )
