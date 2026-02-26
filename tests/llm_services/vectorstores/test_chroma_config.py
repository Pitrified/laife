"""Unit tests for ChromaConfig - no network or disk I/O required."""

from laife.llm_services.vectorstores.cchroma import CChroma
from laife.llm_services.vectorstores.config.base import VectorStoreConfig
from laife.llm_services.vectorstores.config.chroma import ChromaConfig
from laife.llm_services.vectorstores.entity_store import EntityStore

# ---------------------------------------------------------------------------
# ChromaConfig construction
# ---------------------------------------------------------------------------


def test_chroma_config_defaults() -> None:
    """ChromaConfig must be constructable with no arguments."""
    config = ChromaConfig()
    assert config.collection_name == "laife"
    assert config.persist_directory is None
    assert config.host is None
    assert config.port is None
    assert config.ssl is False
    assert config.embeddings_config is None


def test_chroma_config_is_vector_store_config() -> None:
    """ChromaConfig must satisfy the VectorStoreConfig contract."""
    assert issubclass(ChromaConfig, VectorStoreConfig)


# ---------------------------------------------------------------------------
# create_vector_store  - ephemeral in-memory Chroma
# ---------------------------------------------------------------------------


def test_create_vector_store_returns_cchroma() -> None:
    """create_vector_store() must return a CChroma instance."""
    config = ChromaConfig()
    store = config.create_vector_store()
    assert isinstance(store, CChroma)


def test_create_vector_store_uses_collection_name() -> None:
    """The collection name from the config must be forwarded to CChroma."""
    config = ChromaConfig(collection_name="test_collection")
    store = config.create_vector_store()
    assert store._collection.name == "test_collection"


# ---------------------------------------------------------------------------
# EntityStore integration
# ---------------------------------------------------------------------------


def test_entity_store_accepts_vector_store_config() -> None:
    """EntityStore must initialise from a VectorStoreConfig, not a raw CChroma."""
    config = ChromaConfig(collection_name="entity_test")
    es = EntityStore(config)
    assert isinstance(es._db, CChroma)
