# Configurable Vector Store

## Context

`ChatConfig` / `EmbeddingsConfig` both follow the same pattern:

- a `BaseModelKwargs` subclass holds typed, env-readable fields
- a single `create_*()` factory method returns the live object
- provider subclasses (e.g. `ChatOpenAIConfig`) fill in defaults and any extra fields

`CChroma` has no equivalent config layer.
Callers build it ad-hoc with raw constructor kwargs, making it impossible to drive
from env vars, swap providers, or compose with `EntityStore` cleanly.

Unlike `init_chat_model` / `init_embeddings`, LangChain has no `init_vector_store`
helper, so `create_vector_store` must be abstract on the base and implemented in
each concrete subclass.

ref: `.venv/lib/python3.13/site-packages/langchain_chroma/vectorstores.py`

## Goal

Mirror the `chat/config/` and `embeddings/config/` pattern for vector stores:

- `VectorStoreConfig` - abstract base with a `create_vector_store()` factory
- `ChromaConfig` - concrete Chroma subclass (local, persistent, or server)
- Update `EntityStore` to accept a `VectorStoreConfig` instead of a raw `CChroma`

## Design

### 1. `VectorStoreConfig` - `src/laife/llm_services/vectorstores/config/base.py`

```python
from abc import ABC, abstractmethod
from laife.data_models.basemodel_kwargs import BaseModelKwargs
from laife.llm_services.embeddings.config.base import EmbeddingsConfig
from laife.llm_services.vectorstores.cchroma import CChroma


class VectorStoreConfig(BaseModelKwargs, ABC):
    """Abstract base config for a vector store."""

    collection_name: str = "laife"
    embeddings_config: EmbeddingsConfig | None = None

    @abstractmethod
    def create_vector_store(self) -> CChroma: ...
```

Fields kept to a minimum - only the two that are truly provider-agnostic.
`embeddings_config` is forwarded to the concrete store the same way `CChroma.__init__`
already accepts it today.

### 2. `ChromaConfig` - `src/laife/llm_services/vectorstores/config/chroma.py`

Covers the three common Chroma deployment modes (in-memory, local persistent, server):

```python
from laife.llm_services.vectorstores.config.base import VectorStoreConfig
from laife.llm_services.vectorstores.cchroma import CChroma


class ChromaConfig(VectorStoreConfig):
    """Config for a local or server-backed Chroma vector store."""

    # local persistent store
    persist_directory: str | None = None

    # remote / server
    host: str | None = None
    port: int | None = None
    ssl: bool = False

    def create_vector_store(self) -> CChroma:
        return CChroma(
            embeddings_config=self.embeddings_config,
            collection_name=self.collection_name,
            persist_directory=self.persist_directory,
            host=self.host,
            port=self.port,
            ssl=self.ssl,
        )
```

Fields are nullable so that unused deployment modes don't pollute the config.
`CChroma` already ignores `None` kwargs when forwarding to `Chroma.__init__`.

### 3. Update `EntityStore` - `src/laife/llm_services/vectorstores/entity_store.py`

Replace the `CChroma` constructor arg with `VectorStoreConfig`:

```python
# before
def __init__(self, vector_db: CChroma) -> None:
    self._db = vector_db

# after
def __init__(self, config: VectorStoreConfig) -> None:
    self._db = config.create_vector_store()
```

`EntityStore` no longer needs to import `CChroma` directly.

### 4. `__init__.py` exports

Re-export from `src/laife/llm_services/vectorstores/__init__.py`:

```python
from laife.llm_services.vectorstores.config.base import VectorStoreConfig
from laife.llm_services.vectorstores.config.chroma import ChromaConfig
```

## Steps

- [x] Create `src/laife/llm_services/vectorstores/config/__init__.py`
- [x] Create `src/laife/llm_services/vectorstores/config/base.py`
- [x] Create `src/laife/llm_services/vectorstores/config/chroma.py`
- [x] Update `EntityStore.__init__` to accept `VectorStoreConfig`
- [x] Update `src/laife/llm_services/vectorstores/__init__.py` exports
- [x] Grep for all `EntityStore(` / `CChroma(` call sites and update them
- [x] Add tests for `ChromaConfig.create_vector_store()` (in-memory ephemeral client)
