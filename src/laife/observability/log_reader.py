"""Parse and tail the structured JSONL log written by ``laife.meta.logger``.

Pure, Textual-independent: no dependency on the TUI so it can be unit-tested
and reused by any future consumer of the struct log.
"""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dataclasses import field
import datetime
import json
from pathlib import Path
from typing import Any

DEFAULT_CACHE_DIR = Path("cache")

# How often to poll the file for newly appended lines while tailing.
POLL_INTERVAL_SECONDS = 0.25


@dataclass
class LogRow:
    """One parsed record from the structured JSONL log."""

    time: datetime.datetime
    level: str
    message: str
    event: str | None
    player: str | None
    turn: int | None
    extra: dict[str, Any] = field(default_factory=dict)


def latest_log_file(cache_dir: Path | str = DEFAULT_CACHE_DIR) -> Path | None:
    """Return the newest ``game_*.jsonl`` file in *cache_dir*, or None if there isn't one.

    Filenames are ``game_<YYYYMMDDTHHMMSS>.jsonl``, so lexicographic sort order
    matches chronological order.
    """
    candidates = sorted(Path(cache_dir).glob("game_*.jsonl"))
    return candidates[-1] if candidates else None


def _parse_line(line: str) -> LogRow | None:
    """Parse one JSONL line into a `LogRow`; return None for blank/malformed lines."""
    line = line.strip()
    if not line:
        return None
    try:
        record = json.loads(line)["record"]
        extra = dict(record["extra"])
        extra.pop("logger_name", None)
        return LogRow(
            time=datetime.datetime.fromtimestamp(
                record["time"]["timestamp"], tz=datetime.UTC
            ),
            level=record["level"]["name"],
            message=record["message"],
            event=extra.pop("event", None),
            player=extra.pop("player", None),
            turn=extra.pop("turn", None),
            extra=extra,
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


async def tail_jsonl(path: Path | str) -> AsyncIterator[LogRow]:
    """Yield `LogRow`s from *path*: existing content first, then newly appended lines.

    Malformed lines are skipped rather than raised, so a single bad record
    does not kill the tail. A line still being written (no trailing newline
    yet) is retried on the next poll rather than parsed truncated.

    Uses plain blocking file I/O in a poll loop rather than a fully async
    file API: the writer (loguru with ``enqueue=True``) appends to a bare
    file from a background thread, not a pipe, so there is nothing to
    `await` on - only polling. Reads are local-disk and line-sized, so the
    brief blocking is negligible for a single-consumer inspector.
    """
    with Path(path).open(encoding="utf-8") as fh:  # noqa: ASYNC230
        while True:
            pos = fh.tell()
            line = fh.readline()
            if not line or not line.endswith("\n"):
                fh.seek(pos)
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue
            row = _parse_line(line)
            if row is not None:
                yield row
