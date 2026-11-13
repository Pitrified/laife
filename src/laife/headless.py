"""Run the game with no window and no provider, for development.

The world and the players are the live game's (:func:`setup_world`), with a
:class:`ScriptedChatConfig` in place of the provider and no renderer. Each
player runs ``max_turns`` turns and the run ends; the structured log is
written wherever :func:`configure_logging` pointed it, ``cache/`` by default,
so ``make tui`` reads it as it reads a live run.

What it does not show: anything drawn on screen, and how a real model
behaves. The script exercises the engine's code paths, not the prompts.
"""

import asyncio
from contextlib import suppress
import random

from laife.entities.world_runner import WorldRunner
from laife.entities.world_setup import PLAYER_NAMES
from laife.entities.world_setup import setup_world
from laife.llm.scripted_chat import ScriptedChatConfig
from laife.llm.scripted_chat import default_script


class WorldStoppedError(Exception):
    """The world loop returned while players were still playing."""

    def __init__(self) -> None:
        """Say what stopped."""
        super().__init__("WorldRunner.simulate() returned before the players finished")


def scripted_chat_configs() -> dict[str, ScriptedChatConfig]:
    """Give each player the default script, interacting with the next player."""
    return {
        name: ScriptedChatConfig(
            script=default_script(PLAYER_NAMES[(i + 1) % len(PLAYER_NAMES)]),
        )
        for i, name in enumerate(PLAYER_NAMES)
    }


async def run_headless(*, turns: int, seed: int) -> WorldRunner:
    """Play *turns* turns per player in the seeded world and return the runner.

    The world loop is cancelled once every player has returned. If the world
    loop dies first, its exception is raised here: the players would otherwise
    wait on their world requests forever. Call :func:`configure_logging` first
    to choose where the log goes.
    """
    runner = WorldRunner(chat_config=ScriptedChatConfig())
    setup_world(
        runner,
        None,
        random.Random(seed),  # noqa: S311
        chat_configs=scripted_chat_configs(),
    )
    world = asyncio.create_task(runner.simulate())
    players = asyncio.gather(*[player.play(max_turns=turns) for player in runner.players])
    try:
        await asyncio.wait({world, players}, return_when=asyncio.FIRST_COMPLETED)
        if world.done():
            # The world loop only ends by raising; the players would wait on it forever.
            players.cancel()
            with suppress(asyncio.CancelledError):
                await players
            world.result()
            raise WorldStoppedError
        await players
    finally:
        world.cancel()
        with suppress(asyncio.CancelledError):
            await world
    return runner
