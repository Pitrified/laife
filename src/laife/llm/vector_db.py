"""Custom vector db."""

from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from laife.config.lc_embeddings import LcEmbeddingsConfig
from laife.config.lc_embeddings import OpenAIEmbeddingsConfig
from laife.config.lc_embeddings import SentenceTransformerConfig
from laife.embed.sentence_transformer_embeddings import SentenceTransformersEmbeddings
from laife.llm.hasher import Hasher


def get_document_id(document: Document) -> str:
    """Get document id, as an hash of the document content and metadata."""
    # create a hasher object and hash the document content and metadata
    hasher = Hasher(document.page_content)
    document_id = hasher.update(document.metadata)
    return document_id


def get_document_ids(
    documents: list[Document],
    id_in_metadata: str | None = None,
) -> list[str]:
    """Get document ids, as an existing metadata field or hash of the document content and metadata.

    Args:
        documents (list[Document]): the list of documents.
        id_in_metadata (str, optional): the metadata field to use as id.
            Defaults to None.
    """
    if id_in_metadata is None:
        return [get_document_id(doc) for doc in documents]
    return [doc.metadata[id_in_metadata] for doc in documents]


class VectorDB(Chroma):
    """Custom vector db."""

    def __init__(
        self,
        embeddings_config: LcEmbeddingsConfig | None = None,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize the vector database.

        This is unreadable just pass the embeddings_function as an argument.
        """
        match embeddings_config:
            case OpenAIEmbeddingsConfig():
                kwargs["embedding_function"] = OpenAIEmbeddings(
                    **embeddings_config.to_dict(),
                )
            case SentenceTransformerConfig():
                kwargs["embedding_function"] = SentenceTransformersEmbeddings(
                    model_name=embeddings_config.model_name.value,
                )
            case None:
                pass
            case _:
                msg = f"Invalid embeddings config {embeddings_config}"
                raise ValueError(msg)
        super().__init__(*args, **kwargs)

    def add_documents(
        self,
        documents: list[Document],
        id_in_metadata: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> list[str]:
        """Add documents, computing unique ids, unless provided in the metadata.

        Will only add documents that are not already in the database.

        Args:
            documents (list[Document]): List of documents to add.
            id_in_metadata (str, optional): Metadata key to use as id. Defaults to None.
            kwargs: Additional keyword arguments to pass to the parent add_documents method.

        Returns:
            list[str]: List of ids of the newly added documents.
        """
        # get the ids of all the documents
        ids = get_document_ids(documents=documents, id_in_metadata=id_in_metadata)
        # get the ids of existing documents
        known_ids_data = self.get(ids=ids, include=[])
        known_ids: list[str] = known_ids_data["ids"]
        # filter and keep only the new ids and documents
        new_ids = [doc_id for doc_id in ids if doc_id not in known_ids]
        zip_docs_ids = zip(documents, ids, strict=False)
        new_docs = [doc for doc, doc_id in zip_docs_ids if doc_id in new_ids]
        # if there are no new documents, return an empty list
        if len(new_ids) == 0:
            return []
        # add the new documents, returning the ids
        return super().add_documents(documents=new_docs, ids=new_ids, **kwargs)
