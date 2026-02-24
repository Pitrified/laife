"""Main module for the game."""

import asyncio
import random

from laife.entities.building_data import BuildingData
from laife.entities.player_agent import PlayerAgent
from laife.entities.world_renderer import WorldRenderer
from laife.entities.world_runner import WorldRunner
from laife.ui.alog import alg


def setup_world(runner: WorldRunner) -> None:
    """Populate the world with players and buildings."""
    player = PlayerAgent(
        "p0",
        position=(random.randint(0, 800), random.randint(0, 600)),  # noqa: S311
        player_type="inu",
        world_input_queue=runner.input_queue,
    )
    runner.add_player(player)
    player = PlayerAgent(
        "p1",
        position=(random.randint(0, 800), random.randint(0, 600)),  # noqa: S311
        player_type="inu",
        world_input_queue=runner.input_queue,
    )
    runner.add_player(player)

    player_pov = (500, 500)
    # a house
    b = BuildingData(
        name="Alex's House",
        building_type="house",
        description="This house belongs to Alex.",
        position=(300, 100),
        size=(120, 40),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    runner.add_building(b)
    # a farm
    b = BuildingData(
        name="Big ol Farm",
        building_type="farm",
        position=(200, 400),
        size=(120, 40),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    runner.add_building(b)
    # a factory
    b = BuildingData(
        name="Utensil shop",
        building_type="factory",
        position=(500, 800),
        size=(120, 40),
    )
    alg.log(f"W: Adding building >>>\n{b.to_prompt(player_pov)}\n<<<")
    runner.add_building(b)

    # add a building that collides with the house (should be rejected)
    b = BuildingData(
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

    # 2. Renderer initialises pygame — must be created before any sprite loading
    renderer = WorldRenderer(runner)

    # 3. Populate world with plain data objects (no pygame needed here)
    setup_world(runner)

    # 4. Run everything concurrently
    await asyncio.gather(
        runner.simulate(),
        renderer.render(),
        *[agent.play() for agent in runner.agents],
    )


if __name__ == "__main__":
    asyncio.run(main())
