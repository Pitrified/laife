# Entities that can be vectorized

Some entities can be generated dynamically by the player and accepted as valid by the world:

- `BuildingType` - no vector coupling today; needs it added
- `Utensil` - already has `to_document` / `from_document`, but is tightly coupled to `CChroma`

## Problem

`Utensil.__init__` accepts a `vector_db: CChroma` and calls `add_to_vdb()` immediately.
`from_document` also requires a `vector_db` to reconstruct the object.
This means an entity cannot exist without a live vector DB, violating SRP and making
testing awkward.

## Goal

Entities own their serialization logic (`to_document` / `from_document`).
A separate store object owns the vector DB and all I/O with it.

## Design

### 1. `Vectorable` protocol - `src/laife/entities/vectorable.py`

A small `Protocol` (or ABC) that both `Utensil` and `BuildingType` will satisfy:

```python
class Vectorable(Protocol):
    def to_document(self) -> Document: ...

    @classmethod
    def from_document(cls, doc: Document) -> Self: ...
```

`to_document` must write `entity_type` into `doc.metadata` as a discriminator.

### 2. Refactor `Utensil` - `src/laife/entities/utensil.py`

- Remove `vector_db: CChroma` from `__init__`
- Remove `add_to_vdb()`
- Remove `vector_db` arg from `from_document` - it returns a plain `Utensil`

### 3. Add `to_document` / `from_document` to `BuildingType` - `src/laife/entities/building.py`

`BuildingType` is a Pydantic `BaseModel`; add the two methods directly on the class.
`entity_type` metadata value → `"building_type"`.
`size` is a tuple; store as `"size_w"` / `"size_h"` integers in metadata.

### 4. `EntityStore` - `src/laife/llm_services/vectorstores/entity_store.py`

Single class that wraps `CChroma` and knows how to round-trip `Vectorable` objects:

```python
class EntityStore:
    def __init__(self, vector_db: CChroma) -> None: ...

    def save(self, entity: Vectorable) -> None:
        """Convert to Document and upsert into CChroma."""

    def search(self, query: str, k: int = 5) -> list[Document]:
        """Similarity search; callers decode with from_document."""

    def search_typed(self, query: str, entity_type: str, k: int = 5) -> list[Document]:
        """Filtered similarity search by entity_type metadata."""
```

No `load_all` for now - retrieval is always query-driven.

### 5. Registry / dispatcher (optional, later)

A `from_document` dispatcher that reads `entity_type` from metadata and routes to the
correct class can be added as a follow-up if multiple entity types are mixed in one
collection.

## File touch-list

| File                                                  | Change                                                |
| ----------------------------------------------------- | ----------------------------------------------------- |
| `src/laife/entities/vectorable.py`                    | create - `Vectorable` protocol                        |
| `src/laife/entities/utensil.py`                       | remove `vector_db` arg, remove `add_to_vdb`           |
| `src/laife/entities/building.py`                      | add `to_document` / `from_document` to `BuildingType` |
| `src/laife/llm_services/vectorstores/entity_store.py` | create - `EntityStore`                                |
| `src/laife/entities/__init__.py`                      | export `Vectorable`, keep `Utensil`                   |
| `tests/entities/test_vectorable.py`                   | create - unit tests, no live DB needed                |

## Constraints

- Entities must be constructable without any vector DB in scope.
- `CChroma` / `EntityStore` must not be imported inside `entities/` (one-way dependency).
- `from_document` must be a pure `classmethod` that takes only a `Document`.
