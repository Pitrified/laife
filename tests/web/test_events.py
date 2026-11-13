"""The event hub and the log sink that feeds it."""

import asyncio
import datetime as dt
import json
from typing import TYPE_CHECKING

from loguru import logger

from laife.meta.log_events import EVT_ACTION
from laife.meta.logger import configure_logging
from laife.meta.logger import restore_default_logging
from laife.meta.logger import slog
from laife.observability.log_reader import LogRow
from laife.observability.log_reader import parse_line
from laife.web.events import EventHub
from laife.web.events import add_log_sink

if TYPE_CHECKING:
    from pathlib import Path


def make_row(message: str = "m") -> LogRow:
    """Return a minimal row."""
    return LogRow(
        time=dt.datetime(2026, 11, 14, tzinfo=dt.UTC),
        level="INFO",
        message=message,
        event=None,
        player=None,
        turn=None,
    )


def test_publish_numbers_and_fans_out() -> None:
    """Each subscriber gets every event; seq grows by one per publish."""

    async def scenario() -> None:
        hub = EventHub()
        first = hub.subscribe()
        second = hub.subscribe()
        hub.publish(make_row("a"))
        hub.publish(make_row("b"))
        assert hub.seq == 2
        for queue in (first, second):
            events = [queue.get_nowait(), queue.get_nowait()]
            assert [e.seq for e in events if e is not None] == [1, 2]

    asyncio.run(scenario())


def test_slow_subscriber_is_dropped() -> None:
    """A subscriber over the limit gets the drop marker and nothing after."""

    async def scenario() -> None:
        hub = EventHub(queue_size=2)
        queue = hub.subscribe()
        for _ in range(4):
            hub.publish(make_row())
        received = [queue.get_nowait() for _ in range(queue.qsize())]
        assert [e.seq for e in received if e is not None] == [1, 2]
        assert received[-1] is None

    asyncio.run(scenario())


def test_event_json_is_flat_row_with_seq() -> None:
    """The JSON has the row's fields and seq at the top level."""

    async def scenario() -> None:
        event = EventHub().publish(make_row("hello"))
        payload = json.loads(event.to_json())
        assert payload["seq"] == 1
        assert payload["message"] == "hello"
        fields = {"seq", "time", "level", "message", "event", "player", "turn", "extra"}
        assert set(payload) == fields

    asyncio.run(scenario())


def test_sink_publishes_the_row_the_file_holds(tmp_path: Path) -> None:
    """A structured log record reaches the hub as the same row the file parses to."""
    log_file = configure_logging(log_file=tmp_path / "game.jsonl", enqueue=False)

    async def scenario() -> list[LogRow]:
        hub = EventHub()
        queue = hub.subscribe()
        sink_id = add_log_sink(hub)
        try:
            slog.bind(event=EVT_ACTION, player="p0", turn=3, action_type="ActionMove").info(
                EVT_ACTION
            )
        finally:
            logger.remove(sink_id)
        event = queue.get_nowait()
        assert event is not None
        assert event.seq == 1
        return [event.row]

    try:
        rows = asyncio.run(scenario())
    finally:
        restore_default_logging()

    from_file = [parse_line(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    assert rows == from_file
    assert rows[0].player == "p0"
    assert rows[0].extra == {"action_type": "ActionMove"}
