"""Protocol for entities that can be serialized to/from a vector-store Document."""

from typing import Protocol
from typing import Self
from typing import runtime_checkable

from langchain_core.documents import Document


@runtime_checkable
class Vectorable(Protocol):
    """Structural protocol for entities that can round-trip through a Document.

    Implementors must:
    - write ``entity_type`` into ``doc.metadata`` inside ``to_document``.
    - have a pure ``from_document`` that requires **only** the ``Document``
      (no vector-DB reference).
    """

    def to_document(self) -> Document:
        """Serialize the entity to a LangChain Document."""
        ...

    @classmethod
    def from_document(cls, doc: Document) -> Self:
        """Reconstruct an entity from a LangChain Document."""
        ...
