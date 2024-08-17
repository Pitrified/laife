"""Main module for the game."""

import asyncio
from typing import NoReturn

from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

from laife.config.constants import LANGCHAIN_CACHE_DB
from laife.entities.world import World

set_llm_cache(SQLiteCache(database_path=str(LANGCHAIN_CACHE_DB)))


async def main() -> NoReturn:
    """Main function."""
    world = World()
    await world.main_loop()


if __name__ == "__main__":
    # Run the main loop
    asyncio.run(main())
