"""Custom vector db."""

import hashlib
import json
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from loguru import logger as lg


def get_document_id(document: Document) -> str:
    """Get document id, as an hash of the document content and metadata."""
    # get the page content and metadata from the document
    pc = document.page_content
    md = document.metadata
    # create a hash object
    hash_object = hashlib.sha256()
    # set the chunk size for hashing the document content
    chunk_size = 4096
    # update the hash object with the document content in chunks
    for i in range(0, len(pc), chunk_size):
        chunk = pc[i : i + chunk_size]
        hash_object.update(chunk.encode("utf-8"))
    # update the hash object with the serialized metadata
    hash_object.update(json.dumps(md, sort_keys=True).encode("utf-8"))
    # get the hexadecimal representation of the hash
    document_id = hash_object.hexdigest()
    return document_id


class VectorDB(Chroma):
    """Custom vector db."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)

    def add_documents(
        self,
        documents: list[Document],
        id_in_metadata: str = "",
        **kwargs: Any,
    ) -> list[str]:
        """Add documents, computing unique ids, unless provided in the metadata.

        Will only add documents that are not already in the database.

        Args:
            documents (list[Document]): List of documents to add.
            id_in_metadata (str, optional): Metadata key to use as id. Defaults to "".

        Returns:
            list[str]: List of ids of the newly added documents.
        """
        # compute or get the metadata
        if id_in_metadata == "":
            ids = [get_document_id(doc) for doc in documents]
        else:
            ids: list[str] = [doc.metadata[id_in_metadata] for doc in documents]
        # use self.get to check if the document already exists
        known_ids_data = self.get(ids=ids, include=[])
        known_ids: list[str] = known_ids_data["ids"]
        # get the new ids and documents
        new_ids = [doc_id for doc_id in ids if doc_id not in known_ids]
        new_docs = [doc for doc, doc_id in zip(documents, ids) if doc_id in new_ids]
        # if there are no new documents, return an empty list
        if len(new_ids) == 0:
            return []
        # add the new documents, returning the ids
        return super().add_documents(documents=new_docs, ids=new_ids, **kwargs)
