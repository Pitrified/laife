"""Stopping a serving run while a client holds the event stream open."""

import asyncio
import signal
import time
from typing import TYPE_CHECKING

import httpx
import pytest

from laife.entities.sim_control import SimControl
from laife.headless import build_world
from laife.headless import serve_headless
from laife.meta.logger import configure_logging
from laife.meta.logger import restore_default_logging
from laife.web.events import EventHub
from laife.web.server import create_app
from tests.serving import STARTUP_SECONDS
from tests.serving import free_port
from tests.serving import start_serving

if TYPE_CHECKING:
    from pathlib import Path

STOP_SECONDS = 10
"""How long a stop may take before the test calls it a hang."""


async def wait_until_up(client: httpx.AsyncClient) -> None:
    """Poll ``/state`` until the server answers, for at most ``STARTUP_SECONDS``."""
    async with asyncio.timeout(STARTUP_SECONDS):
        while True:
            try:
                await client.get("/state")
            except httpx.TransportError:
                await asyncio.sleep(0.1)
            else:
                return


async def read_until_end(response: httpx.Response) -> None:
    """Read the stream until the server ends it."""
    async for _line in response.aiter_lines():
        pass


def test_close_ends_every_stream() -> None:
    """Closing the hub ends open subscriptions and any made afterwards."""

    async def scenario() -> None:
        hub = EventHub()
        before = hub.subscribe()
        hub.close()
        assert before.get_nowait() is None
        assert hub.subscribe().get_nowait() is None

    asyncio.run(scenario())


def test_quit_route_closes_streams_and_asks_to_stop() -> None:
    """POST /control/quit answers, ends open streams, and sets the stop flag."""

    async def scenario() -> None:
        hub = EventHub()
        app = create_app(build_world(0, SimControl()), None, hub)
        open_stream = hub.subscribe()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/control/quit")
        assert response.json() == {"stopping": True}
        assert open_stream.get_nowait() is None
        assert app.state.stopping.is_set()

    asyncio.run(scenario())


def test_quit_with_stream_open_stops_the_run(tmp_path: Path) -> None:
    """With a client on /events, POST /control/quit makes serve_headless return."""
    configure_logging(log_file=tmp_path / "game.jsonl", enqueue=False)
    port = free_port()

    async def scenario() -> None:
        run = asyncio.create_task(
            serve_headless(turns=None, seed=0, pace=0.05, paused=False, port=port)
        )
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}") as client:
            await wait_until_up(client)
            async with client.stream("GET", "/events") as response:
                await client.post("/control/quit")
                await asyncio.wait_for(read_until_end(response), STOP_SECONDS)
        await asyncio.wait_for(run, STOP_SECONDS)

    try:
        asyncio.run(scenario())
    finally:
        restore_default_logging()


@pytest.mark.parametrize("how", ["sigint", "quit"])
def test_stop_with_stream_open_ends_the_process(tmp_path: Path, how: str) -> None:
    """Ctrl-C or the quit route, with a client on /events: the process exits cleanly and quickly."""
    port = free_port()
    proc = start_serving(tmp_path, port)

    async def open_stream_and_stop() -> None:
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}") as client:
            await wait_until_up(client)
            async with client.stream("GET", "/events") as response:
                if how == "sigint":
                    proc.send_signal(signal.SIGINT)
                else:
                    await client.post("/control/quit")
                await asyncio.wait_for(read_until_end(response), STOP_SECONDS)

    try:
        asyncio.run(open_stream_and_stop())
        start = time.monotonic()
        output, _ = proc.communicate(timeout=STOP_SECONDS)
        assert time.monotonic() - start < STOP_SECONDS
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate()
    assert proc.returncode == 0
    assert "Traceback" not in output
    assert "stopped" in output
