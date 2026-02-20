"""Utensils for the player to use."""

from langchain_core.documents import Document

from laife.llm_services.vectorstores.cchroma import CChroma


class Utensil:
    """An utensil the player can use."""

    def __init__(
        self,
        name: str,
        description: str,
        vector_db: CChroma,
    ) -> None:
        """Initialize an utensil with a name, description and vector DB."""
        self.name = name
        self.description = description
        self.vector_db = vector_db

        self.add_to_vdb()

    def __str__(self) -> str:
        """Return the utensil's display name."""
        return self.name

    def __repr__(self) -> str:
        """Return the developer representation of the utensil."""
        return f"{self.name}: {self.description}"

    def to_prompt(self) -> str:
        """Return a short prompt describing the utensil."""
        return f"{self.name}: {self.description}"

    def to_document(self) -> Document:
        """Convert the utensil to a document."""
        meta = {
            "name": self.name,
            "description": self.description,
            "entity_type": "utensil",
        }
        return Document(
            page_content=self.to_prompt(),
            metadata=meta,
        )

    @classmethod
    def from_document(cls, doc: Document, vector_db: CChroma) -> "Utensil":
        """Create an utensil from a document."""
        return cls(
            name=doc.metadata["name"],
            description=doc.metadata["description"],
            vector_db=vector_db,
        )

    def add_to_vdb(self) -> None:
        """Add the utensil to the vector db."""
        utensil_doc = self.to_document()
        self.vector_db.add_documents([utensil_doc])
