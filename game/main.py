"""Main module for the game."""

import asyncio
import random
from typing import NoReturn

from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

from laife.config.constants import LANGCHAIN_CACHE_DB
from laife.entities.building import Building
from laife.entities.player import Player
from laife.entities.world import World
from laife.ui.alog import alg

set_llm_cache(SQLiteCache(database_path=str(LANGCHAIN_CACHE_DB)))


def setup_world(world: World) -> None:
    """Setup the world."""
    player = Player(
        f"p0",
        position=(random.randint(0, 800), random.randint(0, 600)),
        player_type="inu",
        world_input_queue=world.input_queue,
    )
    world.add_player(player)
    player = Player(
        f"p1",
        position=(random.randint(0, 800), random.randint(0, 600)),
        player_type="inu",
        world_input_queue=world.input_queue,
    )
    world.add_player(player)

    player_pov = (500, 500)
    # a house
    b = Building(
        "Alex's House",
        "house",
        "This house belongs to Alex.",
        (300, 100),
        (120, 40),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    world.add_building(b)
    # a farm
    b = Building(
        "Big ol Farm",
        "farm",
        None,
        (200, 400),
        (120, 40),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    world.add_building(b)
    # a factory
    b = Building(
        "Tool shop",
        "factory",
        None,
        (500, 800),
        (120, 40),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    world.add_building(b)

    # add a building that collides with the house
    b = Building(
        "Colliding House",
        "house",
        None,
        (300, 100),
        (120, 40),
    )
    resp = world.add_building(b)
    alg.log(f"W: Add colliding building response: {resp}")


async def main() -> NoReturn:
    """Main function."""
    world = World()

    setup_world(world)

    await world.simulate()


if __name__ == "__main__":
    # Run the main loop
    asyncio.run(main())
