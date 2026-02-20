"""Main module for the game."""

import asyncio
import random

from laife.entities.building import Building
from laife.entities.player import Player
from laife.entities.world import World
from laife.ui.alog import alg


def setup_world(world: World) -> None:
    """Set up the world."""
    player = Player(
        "p0",
        position=(random.randint(0, 800), random.randint(0, 600)),  # noqa: S311
        player_type="inu",
        world_input_queue=world.input_queue,
    )
    world.add_player(player)
    player = Player(
        "p1",
        position=(random.randint(0, 800), random.randint(0, 600)),  # noqa: S311
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


async def main() -> None:
    """Run main function."""
    world = World()

    setup_world(world)

    await world.simulate()


if __name__ == "__main__":
    # Run the main loop
    asyncio.run(main())
