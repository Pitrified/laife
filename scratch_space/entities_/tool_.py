"""Create a bunch of tools for the game."""

# %% imports

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

# %%

vdb.get()
