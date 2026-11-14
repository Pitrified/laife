"""Play a built world while serving it: the loop of ``make run`` and ``make headless SERVE=1``.

The two runs differ only in the world they hand over: the live one's players
call the configured provider, the headless one's a scripted model.
"""

import asyncio
from contextlib import suppress
from typing import TYPE_CHECKING
from typing import Any

from loguru import logger

from laife.meta.log_events import EVT_SIM_CONTROL
from laife.meta.logger import slog
from laife.web.events import EventHub
from laife.web.events import add_log_sink
from laife.web.server import DEFAULT_HOST
from laife.web.server import DEFAULT_PORT
from laife.web.server import create_app
from laife.web.server import serve

if TYPE_CHECKING:
    from laife.entities.sim_control import SimControl
    from laife.entities.world_runner import WorldRunner


class WorldStoppedError(Exception):
    """The world loop returned while players were still playing."""

    def __init__(self) -> None:
        """Say what stopped."""
        super().__init__("WorldRunner.simulate() returned before the players finished")


async def cancel_task(task: asyncio.Future[Any]) -> None:
    """Cancel *task* and wait for it, keeping its cancellation to itself.

    A task already done is left alone: awaiting it would raise its exception
    again, which the caller has already read with ``result()``.
    """
    if task.done():
        return
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


async def serve_run(
    runner: WorldRunner,
    sim_control: SimControl,
    *,
    turns: int | None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Play *runner*'s world, *turns* per player, while serving it, until the server stops.

    The server stops on ``POST /control/quit``, which returns from here, or on
    Ctrl-C, which ends in ``KeyboardInterrupt``. *turns* ``None`` plays
    without end. The players returning does not stop the server, so the final
    state can still be read. A player or the world loop raising is raised
    here. Either way the log gets a ``sim_control`` event with ``state``
    ``stopped``.

    Call ``configure_logging`` first: it removes every log handler, the event
    sink included.
    """
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
            await cancel_task(task)
        slog.bind(event=EVT_SIM_CONTROL, state="stopped").info(EVT_SIM_CONTROL)
        logger.remove(sink_id)
