"""Create a bunch of utensils for the game."""

# %% imports

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from laife.config.constants import EMBEDDING_MODEL
from laife.config.constants import UTENSILS_COLLECTION
from laife.config.constants import VECTORSTORE_FOL
from laife.entities.utensil import Utensil
from laife.llm.vector_db import VectorDB

# %% setup vector db

embedding_function_lc = OpenAIEmbeddings(
    api_key=SecretStr("aaa"),
    model=EMBEDDING_MODEL,
)


vdb = VectorDB(
    collection_name=UTENSILS_COLLECTION,
    embedding_function=embedding_function_lc,
    persist_directory=str(VECTORSTORE_FOL),
)

# %% create utensils

utensil1 = Utensil(
    name="Hammer",
    description="A utensil for hitting things.",
    vector_db=vdb,
)
utensil1  # pyright: ignore[reportUnusedExpression] # noqa: B018

# %% get utensils as a raw result

utensil_res = vdb.get()
utensil_res  # pyright: ignore[reportUnusedExpression] # noqa: B018

# %% convert result to documents

utensil_docs = [
    Document(pc, metadata=meta)
    for pc, meta in zip(utensil_res["documents"], utensil_res["metadatas"], strict=False)
]
utensil_docs  # pyright: ignore[reportUnusedExpression] # noqa: B018

# %% convert documents to utensils

utensils = [Utensil.from_document(doc, vdb) for doc in utensil_docs]
utensils  # pyright: ignore[reportUnusedExpression] # noqa: B018

# %%

# vdb.delete_collection()
