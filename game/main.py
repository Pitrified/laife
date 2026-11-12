"""Main module for the game."""

import asyncio
import random

from laife.entities.sim_control import SimControl
from laife.entities.world_runner import WorldRunner
from laife.entities.world_setup import setup_world
from laife.meta.logger import configure_logging
from laife.rendering.world_renderer import WorldRenderer


async def main() -> None:
    """Run main function."""
    # 0. Structured file logger - call before anything else
    configure_logging(level="INFO")

    # 1. Pure-logic runner (no pygame)
    runner = WorldRunner()

    # 1b. Pause/step gate: renderer triggers it, players block on it
    sim_control = SimControl()

    # 2. Renderer initialises pygame - must be created before any sprite loading
    renderer = WorldRenderer(runner, sim_control)

    # 3. Populate world with plain data objects (no pygame needed here)
    setup_world(runner, sim_control, random.Random())  # noqa: S311

    # 4. Run everything concurrently
    await asyncio.gather(
        runner.simulate(),
        renderer.render(),
        *[player.play() for player in runner.players],
    )


if __name__ == "__main__":
    asyncio.run(main())
