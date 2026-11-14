"""Run the game with no provider, for development.

The world and the players are the live game's (:func:`setup_world`), with a
:class:`ScriptedChatConfig` in place of the provider. The
structured log is written wherever :func:`configure_logging` pointed it,
``cache/`` by default, so ``make tui`` reads it as it reads a live run.

:func:`run_headless` plays a fixed number of turns and returns.
:func:`serve_headless` serves the world over HTTP with
:func:`laife.web.run.serve_run`, the loop the live game uses too.

What it does not show: how a real model behaves. The script exercises the
engine's code paths, not the prompts.
"""

import asyncio
import random

from laife.entities.sim_control import SimControl
from laife.entities.world_runner import WorldRunner
from laife.entities.world_setup import PLAYER_NAMES
from laife.entities.world_setup import setup_world
from laife.llm.scripted_chat import ScriptedChatConfig
from laife.llm.scripted_chat import default_script
from laife.web.run import WorldStoppedError
from laife.web.run import cancel_task
from laife.web.run import serve_run
from laife.web.server import DEFAULT_HOST
from laife.web.server import DEFAULT_PORT


def scripted_chat_configs(pace: float = 0.0) -> dict[str, ScriptedChatConfig]:
    """Give each player the default script, interacting with the next player."""
    return {
        name: ScriptedChatConfig(
            script=default_script(PLAYER_NAMES[(i + 1) % len(PLAYER_NAMES)]),
            pace=pace,
        )
        for i, name in enumerate(PLAYER_NAMES)
    }


def build_world(seed: int, sim_control: SimControl | None, pace: float = 0.0) -> WorldRunner:
    """Return the seeded world, every chain scripted and answering after *pace* seconds."""
    runner = WorldRunner(chat_config=ScriptedChatConfig(pace=pace))
    setup_world(
        runner,
        sim_control,
        random.Random(seed),  # noqa: S311
        chat_configs=scripted_chat_configs(pace),
    )
    return runner


async def run_headless(*, turns: int, seed: int) -> WorldRunner:
    """Play *turns* turns per player in the seeded world and return the runner.

    The world loop is cancelled once every player has returned. If the world
    loop dies first, its exception is raised here: the players would otherwise
    wait on their world requests forever. Call :func:`configure_logging` first
    to choose where the log goes.
    """
    runner = build_world(seed, None)
    world = asyncio.create_task(runner.simulate())
    players = asyncio.gather(*[player.play(max_turns=turns) for player in runner.players])
    try:
        await asyncio.wait({world, players}, return_when=asyncio.FIRST_COMPLETED)
        if world.done():
            # The world loop only ends by raising; the players would wait on it forever.
            await cancel_task(players)
            world.result()
            raise WorldStoppedError
        await players
    finally:
        await cancel_task(world)
    return runner


async def serve_headless(
    *,
    turns: int | None,
    seed: int,
    pace: float,
    paused: bool,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Play the seeded, scripted world while serving it, until the server stops.

    See :func:`laife.web.run.serve_run`, which this hands the world to.
    """
    sim_control = SimControl()
    if paused:
        sim_control.pause()
    runner = build_world(seed, sim_control, pace)
    await serve_run(runner, sim_control, turns=turns, host=host, port=port)
