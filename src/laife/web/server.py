"""The HTTP app that serves the world, and the coroutine that runs it.

Routes:

- ``GET /state``: a :class:`~laife.web.snapshot.WorldSnapshot`.
- ``GET /events``: Server-Sent Events, one :class:`~laife.web.events.WorldEvent`
  per message, its ``seq`` as the message id, and a comment line as a
  heartbeat when nothing happens.
- ``POST /control/pause``, ``/control/resume``, ``/control/step``: drive the
  run's :class:`SimControl` and return whether it is paused; ``409`` when the
  run has none.
- ``POST /control/quit``: stop the server, and with it the run.

Stopping goes one way, whether by the quit route or by Ctrl-C: the hub ends
every event stream, then uvicorn is told to exit. uvicorn waits for open
responses before it stops, and a stream never finishes by itself, so without
the first step an open page would keep the run alive.

Every route is ``async def``. FastAPI runs a plain ``def`` route in a worker
thread, which would read the live game state from outside the event loop.
"""

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

from laife.web.snapshot import WorldSnapshot
from laife.web.snapshot import take_snapshot

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Callable
    from types import FrameType

    from laife.entities.sim_control import SimControl
    from laife.entities.world_runner import WorldRunner
    from laife.web.events import EventHub
    from laife.web.events import Subscription

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8002
HEARTBEAT_SECONDS = 15.0
"""Seconds of silence on the stream before a comment line is sent."""
GRACEFUL_SHUTDOWN_SECONDS = 3
"""How long uvicorn waits for open connections once told to stop.

The streams the hub owns end at once; this bounds any other connection.
"""


class ControlState(BaseModel):
    """Whether the run is paused after a control call."""

    paused: bool


class StopState(BaseModel):
    """The answer to a quit: the server is stopping."""

    stopping: bool


async def event_stream(
    hub: EventHub, queue: Subscription, heartbeat: float = HEARTBEAT_SECONDS
) -> AsyncIterator[str]:
    """Yield SSE messages from *queue* until the hub drops it; unsubscribe on exit."""
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), heartbeat)
            except TimeoutError:
                yield ": heartbeat\n\n"
                continue
            if event is None:
                return
            yield f"id: {event.seq}\ndata: {event.to_json()}\n\n"
    finally:
        hub.unsubscribe(queue)


def create_app(runner: WorldRunner, sim_control: SimControl | None, hub: EventHub) -> FastAPI:
    """Return the app serving *runner*, controlled by *sim_control*, streaming *hub*.

    ``app.state.stopping`` is set by the quit route; :func:`serve` watches it.
    """
    app = FastAPI(title="laife world")
    app.state.stopping = asyncio.Event()

    def control(act: Callable[[SimControl], None]) -> ControlState:
        if sim_control is None:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="This run has no pause control.",
            )
        act(sim_control)
        return ControlState(paused=sim_control.paused)

    @app.get("/state")
    async def state() -> WorldSnapshot:
        return take_snapshot(runner, sim_control, hub.seq)

    @app.get("/events")
    async def events() -> StreamingResponse:
        queue = hub.subscribe()
        return StreamingResponse(
            event_stream(hub, queue),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    @app.post("/control/pause")
    async def pause() -> ControlState:
        return control(lambda sc: sc.pause())

    @app.post("/control/resume")
    async def resume() -> ControlState:
        return control(lambda sc: sc.resume())

    @app.post("/control/step")
    async def step() -> ControlState:
        return control(lambda sc: sc.step())

    @app.post("/control/quit")
    async def quit_run() -> StopState:
        hub.close()
        app.state.stopping.set()
        return StopState(stopping=True)

    return app


class _WorldServer(uvicorn.Server):
    """uvicorn's server, ending the hub's streams when a signal stops it."""

    def __init__(self, config: uvicorn.Config, hub: EventHub) -> None:
        super().__init__(config)
        self._hub = hub
        self._loop = asyncio.get_running_loop()

    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        # A signal handler runs between two steps of the loop; the hub's queues
        # are touched from the loop itself, on its next pass.
        self._loop.call_soon_threadsafe(self._hub.close)
        super().handle_exit(sig, frame)


async def serve(
    app: FastAPI, hub: EventHub, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT
) -> None:
    """Serve *app*, built by :func:`create_app` on *hub*, until it is stopped.

    Run it as a task in the game's loop. The quit route makes it return.
    uvicorn takes over SIGINT and SIGTERM while it serves, shuts down on the
    first one, and raises the signal again once it has stopped; under
    ``asyncio.run`` that arrives as ``KeyboardInterrupt``.
    """
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_config=None,
        access_log=False,
        timeout_graceful_shutdown=GRACEFUL_SHUTDOWN_SECONDS,
    )
    server = _WorldServer(config, hub)

    async def exit_when_asked() -> None:
        await app.state.stopping.wait()
        server.should_exit = True

    watcher = asyncio.create_task(exit_when_asked())
    try:
        await server.serve()
    finally:
        watcher.cancel()
