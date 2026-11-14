"""The HTTP routes, in process and over a real socket."""

import asyncio
from contextlib import suppress
import json
import socket
from typing import TYPE_CHECKING
from typing import Any

import httpx
from loguru import logger
import uvicorn

from laife.entities.sim_control import SimControl
from laife.headless import build_world
from laife.meta.log_events import EVT_ACTION
from laife.meta.logger import configure_logging
from laife.meta.logger import restore_default_logging
from laife.web.events import EventHub
from laife.web.events import add_log_sink
from laife.web.server import create_app
from laife.web.server import event_stream

if TYPE_CHECKING:
    from pathlib import Path

    from fastapi import FastAPI


async def request(app: FastAPI, method: str, path: str) -> httpx.Response:
    """Send one request to *app* in process."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.request(method, path)


def test_state_and_controls() -> None:
    """/state answers, and the controls pause, step and resume the run."""

    async def scenario() -> None:
        sim_control = SimControl()
        hub = EventHub()
        app = create_app(build_world(0, sim_control), sim_control, hub)

        state = (await request(app, "GET", "/state")).json()
        assert state["paused"] is False
        assert {p["name"] for p in state["players"]} == {"p0", "p1"}

        assert (await request(app, "POST", "/control/pause")).json() == {"paused": True}
        assert sim_control.paused
        assert (await request(app, "POST", "/control/step")).json() == {"paused": True}
        assert (await request(app, "POST", "/control/resume")).json() == {"paused": False}
        assert not sim_control.paused

    asyncio.run(scenario())


def test_controls_without_sim_control_conflict() -> None:
    """A run with no pause control answers 409 and says why."""

    async def scenario() -> None:
        app = create_app(build_world(0, None), None, EventHub())
        response = await request(app, "POST", "/control/pause")
        assert response.status_code == httpx.codes.CONFLICT
        assert "no pause control" in response.json()["detail"]
        assert (await request(app, "GET", "/state")).json()["paused"] is None

    asyncio.run(scenario())


def test_heartbeat_when_quiet() -> None:
    """A quiet stream sends a comment line, then stops when the hub drops it."""

    async def scenario() -> None:
        hub = EventHub()
        queue = hub.subscribe()
        stream = event_stream(hub, queue, heartbeat=0.01)
        assert await anext(stream) == ": heartbeat\n\n"
        queue.put_nowait(None)
        assert [chunk async for chunk in stream] == []

    asyncio.run(scenario())


def test_stream_over_socket_carries_a_running_game(tmp_path: Path) -> None:
    """Over a real connection, /events streams the actions of a game being played."""
    configure_logging(log_file=tmp_path / "game.jsonl", enqueue=False)

    async def scenario() -> list[dict[str, Any]]:
        sim_control = SimControl()
        sim_control.pause()
        runner = build_world(0, sim_control)
        hub = EventHub()
        sink_id = add_log_sink(hub)
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        # Listening before uvicorn starts queues the client's connection until it accepts.
        sock.listen()
        port = sock.getsockname()[1]
        config = uvicorn.Config(
            create_app(runner, sim_control, hub), log_config=None, access_log=False
        )
        server = uvicorn.Server(config)
        server_task = asyncio.create_task(server.serve(sockets=[sock]))
        world = asyncio.create_task(runner.simulate())
        players = asyncio.gather(*[p.play(max_turns=2) for p in runner.players])
        events: list[dict[str, Any]] = []
        try:
            async with (
                httpx.AsyncClient(base_url=f"http://127.0.0.1:{port}") as client,
                client.stream("GET", "/events") as response,
            ):
                await client.post("/control/resume")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        events.append(json.loads(line.removeprefix("data: ")))
                        if events[-1]["event"] == EVT_ACTION:
                            break
        finally:
            server.should_exit = True
            await server_task
            for task in (players, world):
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            logger.remove(sink_id)
        return events

    try:
        events = asyncio.run(asyncio.wait_for(scenario(), timeout=30))
    finally:
        restore_default_logging()

    assert events[-1]["event"] == EVT_ACTION
    seqs = [e["seq"] for e in events]
    assert seqs == sorted(seqs)
