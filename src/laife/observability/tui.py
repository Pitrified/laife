"""Textual TUI that tails a laife structured log for live inspection.

A separate, decoupled process: it only ever reads ``cache/game_*.jsonl``
through :mod:`laife.observability.log_reader`. No pygame, no game-loop
coupling. Run with ``make tui`` or ``uv run python -m laife.observability.tui``.
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from rich.text import Text
from textual import work
from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.binding import BindingType
from textual.widgets import DataTable
from textual.widgets import Footer
from textual.widgets import Header

from laife.observability.log_reader import LogRow
from laife.observability.log_reader import latest_log_file
from laife.observability.log_reader import tail_jsonl

COLUMNS = ("time", "player", "turn", "event", "detail")

# Color per event type so the five stages of a turn's chain
# (llm_call -> action -> world_request -> world_response -> mission_transition)
# read at a glance.
EVENT_COLORS = {
    "llm_call": "blue",
    "action": "cyan",
    "world_request": "yellow",
    "world_response": "green",
    "mission_transition": "magenta",
    "mission_start": "bright_magenta",
    "sim_control": "red",
}


# Per-event-type builders for the detail column; unknown events fall back
# to a plain k=v dump of the row's extras.
_DETAIL_BUILDERS: dict[str, Callable[[LogRow], str]] = {
    # Lead with the action type - str(action) alone drops the class name.
    "action": lambda row: (
        f"{row.extra.get('action_type', '')} {row.extra.get('action', '')}".strip()
    ),
    "world_request": lambda row: str(row.extra.get("kind", "")),
    "world_response": lambda row: (
        f"{row.extra.get('kind', '')} status={row.extra.get('status', '')}"
    ),
    "mission_transition": lambda row: f"to_status={row.extra.get('to_status', '')}",
    "mission_start": lambda row: f"objective={row.extra.get('objective', '')}",
    "llm_call": lambda row: (
        f"stage={row.extra.get('stage', '')} model={row.extra.get('model', '')}"
        f" elapsed={row.extra.get('elapsed', '')}"
    ),
    "sim_control": lambda row: f"state={row.extra.get('state', '')}",
}


def _detail(row: LogRow) -> str:
    """Build a one-line, event-specific summary from a row's extra fields.

    Rows with no recognized event fall back to their extras, then to the raw
    log message - startup/non-event lines carry a message but no extras, so
    without this they would render blank.
    """
    builder = _DETAIL_BUILDERS.get(row.event or "")
    if builder is not None:
        return builder(row)
    if row.extra:
        return ", ".join(f"{k}={v}" for k, v in row.extra.items())
    return row.message


def _round_trip_detail(request: LogRow, response: LogRow) -> str:
    """Detail for a collapsed world_request/world_response pair on one line."""
    return (
        f"{request.extra.get('kind', '')} -> {response.extra.get('kind', '')}"
        f" status={response.extra.get('status', '')}"
    )


@dataclass
class _DisplayEntry:
    """One rendered table row: an anchor log row plus display-only collapse state.

    ``anchor`` is the raw row the row maps back to (the request of a collapsed
    pair, otherwise the row itself) - focus-turn reads its ``(player, turn)``.
    ``detail`` may already be a collapsed round-trip string; ``count`` is the
    number of identical consecutive rows folded into this one (the ``xN`` run).
    """

    anchor: LogRow
    event: str
    detail: str
    count: int = 1


def _signature(entry: _DisplayEntry) -> tuple[str | None, str, str]:
    """Run-collapse key: identical consecutive signatures fold into one row."""
    return (entry.anchor.player, entry.event, entry.detail)


class ObservabilityApp(App[None]):
    """Tail a laife structured log and display it as a live, filterable table."""

    CSS = """
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("p", "cycle_player_filter", "Player filter"),
        Binding("e", "cycle_event_filter", "Event filter"),
        Binding("t", "focus_turn", "Focus turn"),
        Binding("c", "clear_filters", "Clear filters"),
        Binding("f", "toggle_follow", "Follow tail"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, log_path: Path | None = None) -> None:
        """Set up the app to tail *log_path* (default: newest cache/game_*.jsonl)."""
        super().__init__()
        resolved_path = log_path if log_path is not None else latest_log_file()
        if resolved_path is None:
            msg = (
                "No cache/game_*.jsonl log file found. Run the game first, or "
                "pass an explicit path."
            )
            raise FileNotFoundError(msg)
        self.log_path: Path = resolved_path

        self._queue: asyncio.Queue[LogRow] = asyncio.Queue()
        self._rows: list[LogRow] = []
        # Anchor row per displayed table row, parallel to the DataTable; maps a
        # cursor position back to its (player, turn) for focus-turn.
        self._displayed_rows: list[LogRow] = []
        self._players: list[str] = []
        self._event_types: list[str] = []
        self._player_filter: str | None = None
        self._event_filter: str | None = None
        self._focus_key: tuple[str, int] | None = None
        self._follow = True

    def compose(self) -> ComposeResult:
        """Lay out the header, log table, and footer with active bindings."""
        yield Header()
        yield DataTable(id="log_table")
        yield Footer()

    def on_mount(self) -> None:
        """Configure the table and start the reader/UI worker pair."""
        table = self.query_one(DataTable)
        table.add_columns(*COLUMNS)
        table.cursor_type = "row"
        self._read_log()
        self._drain_queue()

    # -- background workers ------------------------------------------------

    @work(exclusive=True, group="reader")
    async def _read_log(self) -> None:
        """Tail the log file and hand every parsed row to the UI worker via a queue.

        Keeps file I/O (including the tail's polling sleep) off the render
        path entirely - this worker never touches widgets directly.
        """
        async for row in tail_jsonl(self.log_path):
            await self._queue.put(row)

    @work(exclusive=True, group="ui")
    async def _drain_queue(self) -> None:
        """Absorb queued rows in batches and rebuild the table once per batch.

        Coalescing everything currently queued into a single rebuild keeps the
        initial load of an existing file O(n) instead of O(n^2), while a live
        tail still refreshes promptly as rows trickle in.
        """
        while True:
            self._absorb(await self._queue.get())
            while True:
                try:
                    self._absorb(self._queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
            self._refresh()

    # -- row handling --------------------------------------------------

    def _absorb(self, row: LogRow) -> None:
        """Record a new raw row and register its player/event for the filters."""
        self._rows.append(row)
        if row.player and row.player not in self._players:
            self._players.append(row.player)
        if row.event and row.event not in self._event_types:
            self._event_types.append(row.event)

    def _passes_filters(self, row: LogRow) -> bool:
        if self._focus_key is not None:
            return (row.player, row.turn) == self._focus_key
        if self._player_filter is not None and row.player != self._player_filter:
            return False
        return not (self._event_filter is not None and row.event != self._event_filter)

    @staticmethod
    def _round_trip_key(row: LogRow) -> tuple[str, int] | None:
        """Correlation key for collapsing a request/response pair, or None."""
        if row.player is None or row.turn is None:
            return None
        return (row.player, row.turn)

    def _build_display(self) -> list[_DisplayEntry]:
        """Filter, pair-collapse, then run-collapse the raw rows into entries.

        Pure over ``self._rows`` and the current filter state; the whole table
        is rebuilt from its result. Both collapses are disabled under turn
        focus, which wants the full, uncollapsed chain. A world_response with no
        pending request (e.g. attached mid-run) or whose request is filtered out
        falls through to its own entry.
        """
        collapse = self._focus_key is None
        entries: list[_DisplayEntry] = []
        pending: dict[tuple[str, int], int] = {}
        for row in self._rows:
            if not self._passes_filters(row):
                continue
            key = self._round_trip_key(row)
            if collapse and row.event == "world_response" and key is not None and key in pending:
                request = entries[pending.pop(key)]
                request.detail = _round_trip_detail(request.anchor, row)
                continue
            entries.append(_DisplayEntry(anchor=row, event=row.event or "", detail=_detail(row)))
            if collapse and row.event == "world_request" and key is not None:
                pending[key] = len(entries) - 1
        return self._run_collapse(entries) if collapse else entries

    @staticmethod
    def _run_collapse(entries: list[_DisplayEntry]) -> list[_DisplayEntry]:
        """Fold each player's run of identical entries into one xN row.

        A run tolerates other players' rows interleaving into it: when two
        players move at once their per-step world requests land in the log as
        ``p0, p1, p0, p1, ...``, and a strictly-consecutive fold would collapse
        nothing. Each ``(player, event, detail)`` signature keeps its own open
        run (so different players never merge into one row); a run stays open
        until the *same* player emits a different signature, which ends that
        player's other runs. The folded row keeps the position of its first
        member.
        """
        collapsed: list[_DisplayEntry] = []
        open_runs: dict[tuple[str | None, str, str], _DisplayEntry] = {}
        for entry in entries:
            sig = _signature(entry)
            run = open_runs.get(sig)
            if run is not None:
                run.count += 1
            else:
                collapsed.append(entry)
                open_runs[sig] = entry
            player = entry.anchor.player
            for other in [s for s in open_runs if s[0] == player and s != sig]:
                del open_runs[other]
        return collapsed

    def _refresh(self) -> None:
        """Rebuild the table from the current raw rows and filter state."""
        entries = self._build_display()
        table = self.query_one(DataTable)
        table.clear()
        self._displayed_rows = [entry.anchor for entry in entries]
        for entry in entries:
            detail = entry.detail if entry.count == 1 else f"{entry.detail} (x{entry.count})"
            event_text = Text(entry.event, style=EVENT_COLORS.get(entry.event, "white"))
            table.add_row(
                entry.anchor.time.strftime("%H:%M:%S.%f")[:-3],
                entry.anchor.player or "-",
                entry.anchor.turn if entry.anchor.turn is not None else "-",
                event_text,
                detail,
            )
        if self._follow and table.row_count:
            table.move_cursor(row=table.row_count - 1)

    # -- actions ------------------------------------------------------

    def action_cycle_player_filter(self) -> None:
        """Cycle the player filter through: all -> each known player -> all."""
        self._focus_key = None
        options: list[str | None] = [None, *sorted(self._players)]
        idx = options.index(self._player_filter) if self._player_filter in options else 0
        self._player_filter = options[(idx + 1) % len(options)]
        self._refresh()

    def action_cycle_event_filter(self) -> None:
        """Cycle the event-type filter through: all -> each known event type -> all."""
        self._focus_key = None
        options: list[str | None] = [None, *sorted(self._event_types)]
        idx = options.index(self._event_filter) if self._event_filter in options else 0
        self._event_filter = options[(idx + 1) % len(options)]
        self._refresh()

    def action_focus_turn(self) -> None:
        """Narrow the view to the (player, turn) of the currently selected row.

        This is the correlation-tracking payoff from phase 1: one keypress
        shows the full llm_call -> action -> world_request -> world_response
        -> mission_transition chain for a single turn.
        """
        table = self.query_one(DataTable)
        cursor_row = table.cursor_row
        if cursor_row is None or cursor_row >= len(self._displayed_rows):
            return
        row = self._displayed_rows[cursor_row]
        if row.player is None or row.turn is None:
            return
        self._player_filter = None
        self._event_filter = None
        self._focus_key = (row.player, row.turn)
        self._refresh()

    def action_clear_filters(self) -> None:
        """Drop the player filter, event filter, and turn focus."""
        self._player_filter = None
        self._event_filter = None
        self._focus_key = None
        self._refresh()

    def action_toggle_follow(self) -> None:
        """Toggle whether new rows auto-scroll the cursor to the bottom."""
        self._follow = not self._follow


def main() -> None:
    """Entry point for `make tui` / `python -m laife.observability.tui`."""
    ObservabilityApp().run()


if __name__ == "__main__":
    main()
