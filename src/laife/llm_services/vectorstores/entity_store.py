"""Store for vectorable entities backed by CChroma."""

from langchain_core.documents import Document

from laife.entities.vectorable import Vectorable
from laife.llm_services.vectorstores.config.base import VectorStoreConfig


class EntityStore:
    """Thin facade around CChroma that speaks in ``Vectorable`` entities.

    Entities themselves have zero knowledge of this class.  The store is the
    only place that holds a reference to the vector DB and performs I/O.
    """

    def __init__(self, config: VectorStoreConfig) -> None:
        """Initialise the store by creating a vector DB from *config*."""
        self._db = config.create_vector_store()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, entity: Vectorable) -> None:
        """Convert *entity* to a Document and upsert it into the vector DB."""
        doc = entity.to_document()
        self._db.add_documents([doc])

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def search(self, query: str, k: int = 5) -> list[Document]:
        """Similarity search returning raw Documents.

        Callers are responsible for deserialising the results via the
        appropriate ``from_document`` classmethod.

        Args:
            query: Free-text similarity query.
            k: Maximum number of results to return.

        Returns:
            Up to *k* Documents ranked by similarity.
        """
        return self._db.similarity_search(query, k=k)

    def search_typed(
        self,
        query: str,
        entity_type: str,
        k: int = 5,
    ) -> list[Document]:
        """Similarity search filtered to a single entity type.

        Args:
            query: Free-text similarity query.
            entity_type: Value that must match the ``entity_type`` metadata
                field (e.g. ``"utensil"`` or ``"building_type"``).
            k: Maximum number of results to return.

        Returns:
            Up to *k* Documents ranked by similarity.
        """
        return self._db.similarity_search(
            query,
            k=k,
            filter={"entity_type": entity_type},
        )
