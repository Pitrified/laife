"""Tests for laife.observability.log_reader."""

import asyncio
import json
from pathlib import Path

from laife.observability.log_reader import LogRow
from laife.observability.log_reader import latest_log_file
from laife.observability.log_reader import tail_jsonl

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _envelope(
    *,
    timestamp: float,
    level: str = "INFO",
    message: str = "action",
    extra: dict[str, object],
) -> str:
    """Build one loguru serialize=True JSON line, matching the real sink's shape."""
    record = {
        "time": {"timestamp": timestamp},
        "level": {"name": level},
        "message": message,
        "extra": {"logger_name": "laife", **extra},
    }
    return json.dumps({"text": f"{message}\n", "record": record})


# ---------------------------------------------------------------------------
# latest_log_file
# ---------------------------------------------------------------------------


def test_latest_log_file_returns_none_when_empty(tmp_path: Path) -> None:
    """No game_*.jsonl files in the directory -> None."""
    assert latest_log_file(tmp_path) is None


def test_latest_log_file_picks_newest_by_name(tmp_path: Path) -> None:
    """Filenames sort chronologically, so the lexicographically-last one wins."""
    older = tmp_path / "game_20260101T000000.jsonl"
    newer = tmp_path / "game_20260102T000000.jsonl"
    older.write_text("")
    newer.write_text("")
    assert latest_log_file(tmp_path) == newer


# ---------------------------------------------------------------------------
# tail_jsonl - existing content
# ---------------------------------------------------------------------------


def test_tail_jsonl_parses_existing_lines(tmp_path: Path) -> None:
    """Lines already present when the tail starts are parsed in order."""
    path = tmp_path / "game_20260101T000000.jsonl"
    path.write_text(
        _envelope(
            timestamp=1000.0,
            extra={"event": "action", "player": "Alice", "turn": 3, "action": "move"},
        )
        + "\n"
        + _envelope(
            timestamp=1001.0,
            extra={"event": "world_request", "player": "Alice", "turn": 3, "kind": "WRecMove"},
        )
        + "\n"
    )

    async def _run() -> list[LogRow]:
        rows: list[LogRow] = []
        async for row in tail_jsonl(path):
            rows.append(row)
            if len(rows) == 2:
                break
        return rows

    rows = asyncio.run(_run())

    assert rows[0].event == "action"
    assert rows[0].player == "Alice"
    assert rows[0].turn == 3
    assert rows[0].level == "INFO"
    assert rows[0].extra == {"action": "move"}

    assert rows[1].event == "world_request"
    assert rows[1].extra == {"kind": "WRecMove"}


def test_tail_jsonl_skips_malformed_lines(tmp_path: Path) -> None:
    """A malformed line does not stop the tail or appear as a row."""
    path = tmp_path / "game_20260101T000000.jsonl"
    path.write_text(
        "not json at all\n"
        + _envelope(timestamp=1000.0, extra={"event": "action", "player": "Bob", "turn": 1})
        + "\n"
    )

    async def _run() -> LogRow:
        async for row in tail_jsonl(path):
            return row
        msg = "expected at least one row"
        raise AssertionError(msg)

    row = asyncio.run(_run())
    assert row.player == "Bob"


# ---------------------------------------------------------------------------
# tail_jsonl - live appends
# ---------------------------------------------------------------------------


def test_tail_jsonl_picks_up_appended_line(tmp_path: Path) -> None:
    """A line appended after the tail has started is picked up without restarting."""
    path = tmp_path / "game_20260101T000000.jsonl"
    path.write_text(
        _envelope(timestamp=1000.0, extra={"event": "action", "player": "Alice", "turn": 1})
        + "\n"
    )

    async def _run() -> list[LogRow]:
        rows: list[LogRow] = []
        gen = tail_jsonl(path)

        first = await anext(gen)
        rows.append(first)

        # Append a second line only after the first has already been consumed,
        # proving the generator polls rather than reading the file once.
        with path.open("a", encoding="utf-8") as fh:
            fh.write(
                _envelope(timestamp=1001.0, extra={"event": "action", "player": "Alice", "turn": 2})
                + "\n"
            )

        second = await anext(gen)
        rows.append(second)
        return rows

    rows = asyncio.run(_run())
    assert [row.turn for row in rows] == [1, 2]
