"""Sample use of the custom vector db."""

# %% imports

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from laife.config.constants import VECTORSTORE_FOL
from laife.config.credentials import OPENAI_API_KEY
from laife.llm.vector_db import VectorDB

# %% setup

EMBEDDING_MODEL = "text-embedding-3-small"

# from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
# embedding_function = OpenAIEmbeddingFunction(
#     api_key=OPENAI_API_KEY.get_secret_value(),
#     model_name=EMBEDDING_MODEL,
# )

embedding_function_lc = OpenAIEmbeddings(
    api_key=OPENAI_API_KEY,
    model=EMBEDDING_MODEL,
)


vdb = VectorDB(
    collection_name="test",
    embedding_function=embedding_function_lc,
    persist_directory=str(VECTORSTORE_FOL),
)

# %% add documents

documents = [
    Document(
        page_content="This is a test document",
        metadata={"title": "Test document 1"},
    ),
    Document(
        page_content="This is another test document",
        metadata={"title": "Test document 2"},
    ),
]
vdb.add_documents(documents)

# %%

# adding the documents again will not add them
vdb.add_documents(documents)
