"""Run the game with no window and no provider, for development.

The world and the players are the live game's (:func:`setup_world`), with a
:class:`ScriptedChatConfig` in place of the provider and no renderer. The
structured log is written wherever :func:`configure_logging` pointed it,
``cache/`` by default, so ``make tui`` reads it as it reads a live run.

:func:`run_headless` plays a fixed number of turns and returns.
:func:`serve_headless` serves the world over HTTP (:mod:`laife.web`) and keeps
serving after the players finish, until the server is stopped.

What it does not show: anything drawn on screen, and how a real model
behaves. The script exercises the engine's code paths, not the prompts.
"""

import asyncio
from contextlib import suppress
import random
from typing import Any

from loguru import logger

from laife.entities.sim_control import SimControl
from laife.entities.world_runner import WorldRunner
from laife.entities.world_setup import PLAYER_NAMES
from laife.entities.world_setup import setup_world
from laife.llm.scripted_chat import ScriptedChatConfig
from laife.llm.scripted_chat import default_script
from laife.web.events import EventHub
from laife.web.events import add_log_sink
from laife.web.server import DEFAULT_HOST
from laife.web.server import DEFAULT_PORT
from laife.web.server import create_app
from laife.web.server import serve


class WorldStoppedError(Exception):
    """The world loop returned while players were still playing."""

    def __init__(self) -> None:
        """Say what stopped."""
        super().__init__("WorldRunner.simulate() returned before the players finished")


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


async def _cancel(task: asyncio.Future[Any]) -> None:
    """Cancel *task* and wait for it, keeping its cancellation to itself.

    A task already done is left alone: awaiting it would raise its exception
    again, which the caller has already read with ``result()``.
    """
    if task.done():
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


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
            await _cancel(players)
            world.result()
            raise WorldStoppedError
        await players
    finally:
        await _cancel(world)
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
    """Play the seeded world while serving it, until the server stops.

    The server stops on ``POST /control/quit``, which returns from here, or on
    Ctrl-C, which ends in ``KeyboardInterrupt``. *turns* ``None`` plays
    without end. The players returning does not stop the server, so the final
    state can still be read. A player or the world
    loop raising is raised here. Call :func:`configure_logging` first: it
    removes every log handler, the event sink included.
    """
    sim_control = SimControl()
    if paused:
        sim_control.pause()
    runner = build_world(seed, sim_control, pace)
    hub = EventHub()
    sink_id = add_log_sink(hub)
    server = asyncio.create_task(serve(create_app(runner, sim_control, hub), hub, host, port))
    world = asyncio.create_task(runner.simulate())
    players = asyncio.gather(*[player.play(max_turns=turns) for player in runner.players])
    pending: set[asyncio.Future[Any]] = {server, world, players}
    try:
        while True:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            if players in done:
                players.result()
            if world in done:
                world.result()
                raise WorldStoppedError
            if server in done:
                server.result()
                return
    finally:
        for task in (players, world, server):
            await _cancel(task)
        logger.remove(sink_id)
