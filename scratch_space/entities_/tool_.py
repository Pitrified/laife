"""Create a bunch of tools for the game."""

# %% imports

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from laife.config.constants import EMBEDDING_MODEL, TOOLS_COLLECTION, VECTORSTORE_FOL
from laife.config.credentials import OPENAI_API_KEY
from laife.entities.tool import Tool
from laife.llm.vector_db import VectorDB

# %% setup vector db

embedding_function_lc = OpenAIEmbeddings(
    api_key=OPENAI_API_KEY,
    model=EMBEDDING_MODEL,
)


vdb = VectorDB(
    collection_name=TOOLS_COLLECTION,
    embedding_function=embedding_function_lc,
    persist_directory=str(VECTORSTORE_FOL),
)

# %% create tools

tool1 = Tool(
    name="Hammer",
    description="A tool for hitting things.",
    vector_db=vdb,
)
tool1

# %% get tools as a raw result

tool_res = vdb.get()
tool_res

# %% convert result to documents

tool_docs = [
    Document(pc, metadata=meta)
    for pc, meta in zip(tool_res["documents"], tool_res["metadatas"])
]
tool_docs

# %% convert documents to tools

tools = [Tool.from_document(doc, vdb) for doc in tool_docs]
tools

# %%

# vdb.delete_collection()
