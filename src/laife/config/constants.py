from pathlib import Path

# Path to the root of the project
ROOT_FOL = Path(__file__).parents[3]
STATIC_FOL = ROOT_FOL / "static"
SPRITES_FOL = STATIC_FOL / "sprites"

CACHE_FOL = ROOT_FOL / "cache"

LANGCHAIN_CACHE_DB = CACHE_FOL / ".langchain.db"

DATA_FOL = ROOT_FOL / "data"
VECTORSTORE_FOL = DATA_FOL / "vectorstore"

EMBEDDING_MODEL = "text-embedding-3-small"

TOOLS_COLLECTION = "tools"
