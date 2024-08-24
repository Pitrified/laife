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
        meta = {"name": self.name}
        return Document(
            page_content=self.to_prompt(),
            metadata=meta,
        )

    def add_to_vdb(self) -> None:
        """Add the tool to the vector db."""
        tool_doc = self.to_document()
        self.vector_db.add_documents([tool_doc])
