"""World events for the stream: every structured log record, numbered.

The source is the structured log itself. :func:`add_log_sink` adds a loguru
sink beside the file sink, and each record it receives becomes a
:class:`WorldEvent` with the same fields ``make tui`` reads from the file.
"""

import asyncio
from dataclasses import dataclass
import json
import threading

from loguru import logger
from pydantic import TypeAdapter

from laife.observability.log_reader import LogRow
from laife.observability.log_reader import parse_line

SUBSCRIBER_QUEUE_SIZE = 1000
"""Events a subscriber may fall behind by before it is dropped."""

_ROW_ADAPTER: TypeAdapter[LogRow] = TypeAdapter(LogRow)


@dataclass(frozen=True)
class WorldEvent:
    """One log record, numbered in the order the hub published it."""

    seq: int
    row: LogRow

    def to_json(self) -> str:
        """Return the row's fields and ``seq`` as one flat JSON object."""
        return json.dumps({"seq": self.seq, **_ROW_ADAPTER.dump_python(self.row, mode="json")})


type Subscription = asyncio.Queue[WorldEvent | None]
"""A subscriber's queue; ``None`` in it means the hub dropped the subscriber."""


class EventHub:
    """Numbers events and hands each one to every subscriber.

    ``publish`` never waits. A subscriber more than *queue_size* events behind
    is dropped: it gets ``None`` and nothing after, so a slow client loses its
    stream rather than slowing the game. It is expected to reconnect and fetch
    a fresh snapshot.

    :meth:`close` ends every stream, for a server shutting down: uvicorn waits
    for open responses before it stops, and a stream never finishes by itself.
    """

    def __init__(self, queue_size: int = SUBSCRIBER_QUEUE_SIZE) -> None:
        """Start at ``seq`` 0 with no subscribers."""
        self.seq = 0
        self._queue_size = queue_size
        self._subscribers: set[Subscription] = set()
        self._closed = False

    def subscribe(self) -> Subscription:
        """Return a queue that receives every event published from now on.

        After :meth:`close` the queue holds only the end marker.
        """
        # One slot over the limit, so the drop marker always fits.
        queue: Subscription = asyncio.Queue(maxsize=self._queue_size + 1)
        if self._closed:
            queue.put_nowait(None)
        else:
            self._subscribers.add(queue)
        return queue

    def close(self) -> None:
        """End every open stream and every stream opened afterwards."""
        self._closed = True
        for queue in self._subscribers:
            queue.put_nowait(None)
        self._subscribers.clear()

    def unsubscribe(self, queue: Subscription) -> None:
        """Stop sending to *queue*; a queue already dropped is ignored."""
        self._subscribers.discard(queue)

    def publish(self, row: LogRow) -> WorldEvent:
        """Give *row* the next number, hand it to every subscriber, return the event."""
        self.seq += 1
        event = WorldEvent(seq=self.seq, row=row)
        for queue in list(self._subscribers):
            if queue.qsize() >= self._queue_size:
                self._subscribers.discard(queue)
                queue.put_nowait(None)
            else:
                queue.put_nowait(event)
        return event


def add_log_sink(hub: EventHub, level: str = "INFO") -> int:
    """Publish every log record at *level* or above to *hub*; return the loguru handler id.

    Call it from the event loop's thread, after ``configure_logging``, which
    removes every handler. Records logged on that thread are published at
    once, so a snapshot taken afterwards carries their ``seq``; records from
    any other thread are handed to the loop with ``call_soon_threadsafe``.
    Remove the sink with ``logger.remove(handler_id)``.
    """
    loop = asyncio.get_running_loop()
    loop_thread = threading.get_ident()

    def sink(message: str) -> None:
        row = parse_line(message)
        if row is None:
            return
        if threading.get_ident() == loop_thread:
            hub.publish(row)
        else:
            loop.call_soon_threadsafe(hub.publish, row)

    return logger.add(sink, serialize=True, level=level, enqueue=False)
