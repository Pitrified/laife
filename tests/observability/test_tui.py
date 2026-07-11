"""Tests for laife.observability.tui, using Textual's headless test pilot."""

import asyncio
import json
from pathlib import Path

import pytest
from textual.pilot import Pilot
from textual.widgets import DataTable

from laife.observability.tui import ObservabilityApp

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _envelope(*, timestamp: float, extra: dict[str, object]) -> str:
    """Build one loguru serialize=True JSON line, matching the real sink's shape."""
    record = {
        "time": {"timestamp": timestamp},
        "level": {"name": "INFO"},
        "message": str(extra.get("event", "")),
        "extra": {"logger_name": "laife", **extra},
    }
    return json.dumps({"text": "x\n", "record": record})


def _write_fixture(path: Path) -> None:
    """Write a two-player, two-event fixture, both rows on turn 1."""
    lines = [
        _envelope(
            timestamp=1000.0,
            extra={"event": "action", "player": "Alice", "turn": 1, "action": "move"},
        ),
        _envelope(
            timestamp=1001.0,
            extra={
                "event": "world_response",
                "player": "Alice",
                "turn": 1,
                "kind": "WResMove",
                "status": "success",
            },
        ),
        _envelope(
            timestamp=1002.0,
            extra={"event": "action", "player": "Bob", "turn": 1, "action": "build"},
        ),
    ]
    path.write_text("\n".join(lines) + "\n")


def _round_trip_line(*, timestamp: float, event: str, extra: dict[str, object]) -> str:
    """One request/response envelope for the collapse fixtures."""
    return _envelope(
        timestamp=timestamp,
        extra={"event": event, "player": "Alice", "turn": 1, **extra},
    )


def _request_line() -> str:
    """Build an Alice/turn-1 world_request line (WRecBuild)."""
    return _round_trip_line(timestamp=1000.0, event="world_request", extra={"kind": "WRecBuild"})


def _response_line() -> str:
    """Build the matching Alice/turn-1 world_response line (WResBuild, success)."""
    return _round_trip_line(
        timestamp=1001.0,
        event="world_response",
        extra={"kind": "WResBuild", "status": "success"},
    )


def _move_pair(*, ts: float, player: str = "Alice", turn: int = 1) -> list[str]:
    """Build a WRecMove/WResMove(success) round trip - the repeated move noise."""
    return [
        _envelope(
            timestamp=ts,
            extra={"event": "world_request", "player": player, "turn": turn, "kind": "WRecMove"},
        ),
        _envelope(
            timestamp=ts + 0.1,
            extra={
                "event": "world_response",
                "player": player,
                "turn": turn,
                "kind": "WResMove",
                "status": "success",
            },
        ),
    ]


def _write_lines(path: Path, lines: list[str]) -> None:
    """Write JSON-lines to *path*."""
    path.write_text("\n".join(lines) + "\n")


async def _settle(pilot: Pilot[None]) -> None:
    """Give the reader/UI workers a few ticks to drain the queue."""
    for _ in range(5):
        await pilot.pause()
        await asyncio.sleep(0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_app_raises_when_no_log_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Constructing the app with no log file anywhere is a clear, immediate error."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        ObservabilityApp()


def test_app_loads_existing_rows(tmp_path: Path) -> None:
    """Rows already in the file when the app starts appear in the table."""
    path = tmp_path / "game_20260101T000000.jsonl"
    _write_fixture(path)
    app = ObservabilityApp(log_path=path)

    async def _run() -> int:
        async with app.run_test() as pilot:
            await _settle(pilot)
            return app.query_one(DataTable).row_count

    assert asyncio.run(_run()) == 3


def test_player_filter_narrows_rows(tmp_path: Path) -> None:
    """Cycling the player filter to 'Alice' hides Bob's row."""
    path = tmp_path / "game_20260101T000000.jsonl"
    _write_fixture(path)
    app = ObservabilityApp(log_path=path)

    async def _run() -> tuple[int, str | None]:
        async with app.run_test() as pilot:
            await _settle(pilot)
            await pilot.press("p")  # players sort alphabetically: Alice first
            await _settle(pilot)
            return app.query_one(DataTable).row_count, app._player_filter

    row_count, player_filter = asyncio.run(_run())
    assert player_filter == "Alice"
    assert row_count == 2


def test_clear_filters_restores_all_rows(tmp_path: Path) -> None:
    """After filtering, pressing 'c' clears every filter and shows all rows again."""
    path = tmp_path / "game_20260101T000000.jsonl"
    _write_fixture(path)
    app = ObservabilityApp(log_path=path)

    async def _run() -> int:
        async with app.run_test() as pilot:
            await _settle(pilot)
            await pilot.press("p")
            await _settle(pilot)
            await pilot.press("c")
            await _settle(pilot)
            return app.query_one(DataTable).row_count

    assert asyncio.run(_run()) == 3


def test_focus_turn_shows_only_that_player_turn(tmp_path: Path) -> None:
    """Focusing a row narrows the table to that row's (player, turn) chain."""
    path = tmp_path / "game_20260101T000000.jsonl"
    _write_fixture(path)
    app = ObservabilityApp(log_path=path)

    async def _run() -> tuple[int, tuple[str, int] | None]:
        async with app.run_test() as pilot:
            await _settle(pilot)
            table = app.query_one(DataTable)
            table.move_cursor(row=2)  # Bob's row
            await pilot.press("t")
            await _settle(pilot)
            return table.row_count, app._focus_key

    row_count, focus_key = asyncio.run(_run())
    assert focus_key == ("Bob", 1)
    assert row_count == 1


def test_world_round_trip_collapses_to_one_row(tmp_path: Path) -> None:
    """A world_request and its matching world_response render as one line."""
    path = tmp_path / "game_20260101T000000.jsonl"
    path.write_text(_request_line() + "\n" + _response_line() + "\n")
    app = ObservabilityApp(log_path=path)

    async def _run() -> tuple[int, str]:
        async with app.run_test() as pilot:
            await _settle(pilot)
            table = app.query_one(DataTable)
            return table.row_count, str(table.get_row_at(0)[4])

    row_count, detail = asyncio.run(_run())
    assert row_count == 1
    assert detail == "WRecBuild -> WResBuild status=success"


def test_in_flight_request_shows_alone(tmp_path: Path) -> None:
    """A world_request with no response yet shows on its own line, undisturbed."""
    path = tmp_path / "game_20260101T000000.jsonl"
    path.write_text(_request_line() + "\n")
    app = ObservabilityApp(log_path=path)

    async def _run() -> tuple[int, str]:
        async with app.run_test() as pilot:
            await _settle(pilot)
            table = app.query_one(DataTable)
            return table.row_count, str(table.get_row_at(0)[4])

    row_count, detail = asyncio.run(_run())
    assert row_count == 1
    assert detail == "WRecBuild"


def test_focus_turn_keeps_round_trip_uncollapsed(tmp_path: Path) -> None:
    """Under turn focus the pair stays as two rows, showing the full chain."""
    path = tmp_path / "game_20260101T000000.jsonl"
    path.write_text(_request_line() + "\n" + _response_line() + "\n")
    app = ObservabilityApp(log_path=path)

    async def _run() -> int:
        async with app.run_test() as pilot:
            await _settle(pilot)
            table = app.query_one(DataTable)
            table.move_cursor(row=0)
            await pilot.press("t")  # focus (Alice, 1)
            await _settle(pilot)
            return table.row_count

    assert asyncio.run(_run()) == 2


def test_consecutive_identical_rows_collapse_with_xn(tmp_path: Path) -> None:
    """A run of identical round-trip rows folds into one row with an (xN) suffix."""
    path = tmp_path / "game_20260101T000000.jsonl"
    _write_lines(path, [*_move_pair(ts=1000.0), *_move_pair(ts=1002.0), *_move_pair(ts=1004.0)])
    app = ObservabilityApp(log_path=path)

    async def _run() -> tuple[int, str]:
        async with app.run_test() as pilot:
            await _settle(pilot)
            table = app.query_one(DataTable)
            return table.row_count, str(table.get_row_at(0)[4])

    row_count, detail = asyncio.run(_run())
    assert row_count == 1
    assert detail == "WRecMove -> WResMove status=success (x3)"


def test_differing_row_breaks_the_run(tmp_path: Path) -> None:
    """An unlike row between two identical ones splits them into separate runs."""
    path = tmp_path / "game_20260101T000000.jsonl"
    action = _envelope(
        timestamp=1001.5,
        extra={"event": "action", "player": "Alice", "turn": 1, "action": "move"},
    )
    _write_lines(path, [*_move_pair(ts=1000.0), action, *_move_pair(ts=1002.0)])
    app = ObservabilityApp(log_path=path)

    async def _run() -> int:
        async with app.run_test() as pilot:
            await _settle(pilot)
            return app.query_one(DataTable).row_count

    # move-pair, action, move-pair -> three distinct rows, none collapsed.
    assert asyncio.run(_run()) == 3


def test_interleaved_player_prevents_collapse(tmp_path: Path) -> None:
    """Identical details from different players never merge - the run key includes player."""
    path = tmp_path / "game_20260101T000000.jsonl"
    lines = [*_move_pair(ts=1000.0, player="Alice"), *_move_pair(ts=1002.0, player="Bob")]
    _write_lines(path, lines)
    app = ObservabilityApp(log_path=path)

    async def _run() -> int:
        async with app.run_test() as pilot:
            await _settle(pilot)
            return app.query_one(DataTable).row_count

    assert asyncio.run(_run()) == 2


def test_interleaved_repeats_collapse_per_player(tmp_path: Path) -> None:
    """Two players moving at once interleave in the log yet still fold per player.

    Concurrent movement lands as ``Alice, Bob, Alice, Bob, ...`` in the shared
    world queue; each player's run must still collapse to one xN row rather than
    a wall of alternating rows.
    """
    path = tmp_path / "game_20260101T000000.jsonl"
    lines = [
        *_move_pair(ts=1000.0, player="Alice"),
        *_move_pair(ts=1000.5, player="Bob"),
        *_move_pair(ts=1002.0, player="Alice"),
        *_move_pair(ts=1002.5, player="Bob"),
        *_move_pair(ts=1004.0, player="Alice"),
        *_move_pair(ts=1004.5, player="Bob"),
    ]
    _write_lines(path, lines)
    app = ObservabilityApp(log_path=path)

    async def _run() -> tuple[int, str, str]:
        async with app.run_test() as pilot:
            await _settle(pilot)
            table = app.query_one(DataTable)
            return table.row_count, str(table.get_row_at(0)[4]), str(table.get_row_at(1)[4])

    row_count, alice_detail, bob_detail = asyncio.run(_run())
    assert row_count == 2
    assert alice_detail == "WRecMove -> WResMove status=success (x3)"
    assert bob_detail == "WRecMove -> WResMove status=success (x3)"


def test_focus_turn_shows_repeats_uncollapsed(tmp_path: Path) -> None:
    """Under turn focus, repeated round trips are shown in full, not folded."""
    path = tmp_path / "game_20260101T000000.jsonl"
    _write_lines(path, [*_move_pair(ts=1000.0), *_move_pair(ts=1002.0), *_move_pair(ts=1004.0)])
    app = ObservabilityApp(log_path=path)

    async def _run() -> int:
        async with app.run_test() as pilot:
            await _settle(pilot)
            table = app.query_one(DataTable)
            table.move_cursor(row=0)
            await pilot.press("t")  # focus (Alice, 1)
            await _settle(pilot)
            return table.row_count

    # 3 requests + 3 responses, all shown uncollapsed under focus.
    assert asyncio.run(_run()) == 6


def test_mission_start_row_shows_objective(tmp_path: Path) -> None:
    """A mission_start event renders its objective in the detail column."""
    path = tmp_path / "game_20260101T000000.jsonl"
    _write_lines(
        path,
        [
            _envelope(
                timestamp=1000.0,
                extra={
                    "event": "mission_start",
                    "player": "Alice",
                    "turn": 2,
                    "from_status": "completed",
                    "objective": "build a raft",
                },
            )
        ],
    )
    app = ObservabilityApp(log_path=path)

    async def _run() -> str:
        async with app.run_test() as pilot:
            await _settle(pilot)
            return str(app.query_one(DataTable).get_row_at(0)[4])

    assert asyncio.run(_run()) == "objective=build a raft"


def test_event_less_row_falls_back_to_message(tmp_path: Path) -> None:
    """A log line with no event and no extras shows its message, not a blank cell."""
    path = tmp_path / "game_20260101T000000.jsonl"
    record = {
        "time": {"timestamp": 1000.0},
        "level": {"name": "INFO"},
        "message": "Loading Laife params",
        "extra": {"logger_name": "laife"},
    }
    _write_lines(path, [json.dumps({"text": "x\n", "record": record})])
    app = ObservabilityApp(log_path=path)

    async def _run() -> str:
        async with app.run_test() as pilot:
            await _settle(pilot)
            return str(app.query_one(DataTable).get_row_at(0)[4])

    assert asyncio.run(_run()) == "Loading Laife params"
