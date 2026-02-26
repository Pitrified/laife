"""Utensils for the player to use."""

from langchain_core.documents import Document


class Utensil:
    """An utensil the player can use."""

    def __init__(
        self,
        name: str,
        description: str,
    ) -> None:
        """Initialize an utensil with a name and description."""
        self.name = name
        self.description = description

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
    def from_document(cls, doc: Document) -> "Utensil":
        """Reconstruct an utensil from a LangChain Document."""
        return cls(
            name=doc.metadata["name"],
            description=doc.metadata["description"],
        )
