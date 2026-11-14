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
- ``GET /sprites``: the sprite URL for each player type and state.
- ``/sprites/<type>/<file>``: the sprite images, from ``static/sprites/``.
- ``/vendor/<package>/<file>``: a third-party file listed in ``ui/vendor.toml``,
  checked against its lock on every request (:mod:`laife.web.vendor`); ``404``
  for a file not listed or not fetched, ``500`` for one whose bytes changed.
- ``/``: the page, from ``ui/world_web/``.

Static files go out with ``Cache-Control: no-cache``: a browser keeps them
but asks again on every load, so an edited page shows on the next reload.

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
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from laife.config.sprites import STATE_FNS
from laife.meta.log_events import EVT_SIM_CONTROL
from laife.meta.logger import slog
from laife.params.laife_params import get_laife_params
from laife.web.snapshot import WorldSnapshot
from laife.web.snapshot import take_snapshot
from laife.web.vendor import VendorFileMissingError
from laife.web.vendor import VendorIntegrityError
from laife.web.vendor import load_manifest
from laife.web.vendor import verified_path

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Callable
    import os
    from pathlib import Path
    from types import FrameType

    from starlette.responses import Response
    from starlette.types import Scope

    from laife.entities.sim_control import SimControl
    from laife.entities.world_runner import WorldRunner
    from laife.web.events import EventHub
    from laife.web.events import Subscription

PAGE_NAME = "world_web"
"""The page's folder under ``ui/``."""
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


class NoCacheFiles(StaticFiles):
    """Static files sent with ``Cache-Control: no-cache``."""

    def file_response(
        self,
        full_path: str | os.PathLike[str],
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        """Return the file's response with the cache header set."""
        response = super().file_response(full_path, stat_result, scope, status_code)
        response.headers["Cache-Control"] = "no-cache"
        return response


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


def create_app(
    runner: WorldRunner,
    sim_control: SimControl | None,
    hub: EventHub,
    vendor_cache: Path | None = None,
) -> FastAPI:
    """Return the app serving *runner*, controlled by *sim_control*, streaming *hub*.

    ``app.state.stopping`` is set by the quit route; :func:`serve` watches it.
    *vendor_cache* is where ``make vendor`` put the third-party files,
    ``cache/vendor/`` by default.
    """
    app = FastAPI(title="laife world")
    app.state.stopping = asyncio.Event()
    _add_world_routes(app, runner, sim_control, hub)
    _add_control_routes(app, sim_control, hub)
    # Last: their mount at "/" would otherwise answer every route above.
    _add_file_routes(app, vendor_cache)
    return app


def _add_world_routes(
    app: FastAPI, runner: WorldRunner, sim_control: SimControl | None, hub: EventHub
) -> None:
    """Add ``/state`` and ``/events``."""

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


def _add_control_routes(app: FastAPI, sim_control: SimControl | None, hub: EventHub) -> None:
    """Add pause, resume, step and quit under ``/control/``."""

    def control(act: Callable[[SimControl], None]) -> ControlState:
        if sim_control is None:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="This run has no pause control.",
            )
        act(sim_control)
        return ControlState(paused=sim_control.paused)

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
        slog.bind(event=EVT_SIM_CONTROL, state="quit").info(EVT_SIM_CONTROL)
        hub.close()
        app.state.stopping.set()
        return StopState(stopping=True)


def _add_file_routes(app: FastAPI, vendor_cache: Path | None) -> None:
    """Add the sprite table, the vendored files, the sprite images and the page."""
    manifest = load_manifest()
    paths = get_laife_params().paths

    @app.get("/sprites")
    async def sprites() -> dict[str, dict[str, str]]:
        return {
            player_type: {state: f"/sprites/{player_type}/{fn}" for state, fn in fns.items()}
            for player_type, fns in STATE_FNS.items()
        }

    @app.get("/vendor/{package}/{member:path}")
    async def vendor(package: str, member: str) -> FileResponse:
        try:
            path = verified_path(manifest.package(package), member, vendor_cache)
        except VendorFileMissingError as error:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(error)) from None
        except VendorIntegrityError as error:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(error)
            ) from None
        return FileResponse(path, headers={"Cache-Control": "no-cache"})

    app.mount("/sprites", NoCacheFiles(directory=paths.sprites_fol), name="sprite_files")
    app.mount("/", NoCacheFiles(directory=paths.ui_fol / PAGE_NAME, html=True), name="page")


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
