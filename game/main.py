"""Main module for the game."""

import asyncio
import random

from laife.entities.building import Building
from laife.entities.player import Player
from laife.entities.world_runner import WorldRunner
from laife.rendering.world_renderer import WorldRenderer
from laife.ui.alog import alg


def setup_world(runner: WorldRunner) -> None:
    """Populate the world with players and buildings."""
    player = Player(
        "p0",
        position=(random.randint(0, 800), random.randint(0, 600)),  # noqa: S311
        player_type="inu",
        world_input_queue=runner.input_queue,
    )
    runner.add_player(player)
    player = Player(
        "p1",
        position=(random.randint(0, 800), random.randint(0, 600)),  # noqa: S311
        player_type="inu",
        world_input_queue=runner.input_queue,
    )
    runner.add_player(player)

    player_pov = (500, 500)
    # a house
    b = Building(
        name="Alex's House",
        building_type="house",
        description="This house belongs to Alex.",
        position=(300, 100),
        size=(120, 40),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    runner.add_building(b)
    # a farm
    b = Building(
        name="Big ol Farm",
        building_type="farm",
        position=(200, 400),
        size=(120, 40),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    runner.add_building(b)
    # a factory
    b = Building(
        name="Utensil shop",
        building_type="factory",
        position=(500, 800),
        size=(120, 40),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    runner.add_building(b)

    # add a building that collides with the house (should be rejected)
    b = Building(
        name="Colliding House",
        building_type="house",
        position=(300, 100),
        size=(120, 40),
    )
    resp = runner.add_building(b)
    alg.log(f"W: Add colliding building response: {resp}")


async def main() -> None:
    """Run main function."""
    # 1. Pure-logic runner (no pygame)
    runner = WorldRunner()

    # 2. Renderer initialises pygame - must be created before any sprite loading
    renderer = WorldRenderer(runner)

    # 3. Populate world with plain data objects (no pygame needed here)
    setup_world(runner)

    # 4. Run everything concurrently
    await asyncio.gather(
        runner.simulate(),
        renderer.render(),
        *[player.play() for player in runner.players],
    )


if __name__ == "__main__":
    asyncio.run(main())
