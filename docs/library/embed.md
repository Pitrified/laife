# embed

Embedding support for the vector store.
Source: [`src/laife/embed/`](https://github.com/Pitrified/laife/tree/main/src/laife/embed).

## Sentence-transformers wrapper

[`sentence_transformer_embeddings.py`](https://github.com/Pitrified/laife/blob/main/src/laife/embed/sentence_transformer_embeddings.py) defines `SentenceTransformersEmbeddings`, a LangChain `Embeddings` implementation backed by HuggingFace `sentence-transformers`.
It is a local port adapted from LangChain's HuggingFace partner package, kept here to avoid the dependency issues that came with routing through ollama.

[`utils.py`](https://github.com/Pitrified/laife/blob/main/src/laife/embed/utils.py) holds the supporting helpers.

World entities such as buildings, terrain, and utensils serialize to LangChain documents in [the entities package](entities.md); these embeddings turn that text into vectors for retrieval, configured through [the vector search params](params.md).
