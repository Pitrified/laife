"""Tools for the player to use."""

from langchain_core.documents import Document

from laife.llm.vector_db import VectorDB


class Tool:
    """A tool the player can use."""

    def __init__(
        self,
        name: str,
        description: str,
        vector_db: VectorDB,
    ) -> None:
        self.name = name
        self.description = description
        self.vector_db = vector_db

        self.add_to_vdb()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.name}: {self.description}"

    def to_prompt(self) -> str:
        return f"{self.name}: {self.description}"

    def to_document(self) -> Document:
        """Convert the tool to a document."""
        meta = {
            "name": self.name,
            "description": self.description,
            "entity_type": "tool",
        }
        return Document(
            page_content=self.to_prompt(),
            metadata=meta,
        )

    @classmethod
    def from_document(cls, doc: Document, vector_db: VectorDB) -> "Tool":
        """Create a tool from a document."""
        return cls(
            name=doc.metadata["name"],
            description=doc.metadata["description"],
            vector_db=vector_db,
        )

    def add_to_vdb(self) -> None:
        """Add the tool to the vector db."""
        tool_doc = self.to_document()
        self.vector_db.add_documents([tool_doc])
