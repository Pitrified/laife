"""Textual TUI that tails a laife structured log for live inspection.

A separate, decoupled process: it only ever reads ``cache/game_*.jsonl``
through :mod:`laife.observability.log_reader`. No pygame, no game-loop
coupling. Run with ``make tui`` or ``uv run python -m laife.observability.tui``.
"""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from rich.text import Text
from textual import work
from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.binding import BindingType
from textual.coordinate import Coordinate
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
    "llm_call": lambda row: (
        f"stage={row.extra.get('stage', '')} model={row.extra.get('model', '')}"
        f" elapsed={row.extra.get('elapsed', '')}"
    ),
    "sim_control": lambda row: f"state={row.extra.get('state', '')}",
}


def _detail(row: LogRow) -> str:
    """Build a one-line, event-specific summary from a row's extra fields."""
    builder = _DETAIL_BUILDERS.get(row.event or "")
    if builder is not None:
        return builder(row)
    return ", ".join(f"{k}={v}" for k, v in row.extra.items())


def _round_trip_detail(request: LogRow, response: LogRow) -> str:
    """Detail for a collapsed world_request/world_response pair on one line."""
    return (
        f"{request.extra.get('kind', '')} -> {response.extra.get('kind', '')}"
        f" status={response.extra.get('status', '')}"
    )


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
        self._displayed_rows: list[LogRow] = []
        # (player, turn) -> index in _displayed_rows of a shown world_request
        # awaiting its world_response, so the pair collapses to one line.
        self._pending_round_trips: dict[tuple[str, int], int] = {}
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
        """Consume queued rows and apply them to the table, one at a time."""
        while True:
            row = await self._queue.get()
            self._ingest(row)

    # -- row handling --------------------------------------------------

    def _ingest(self, row: LogRow) -> None:
        self._rows.append(row)
        if row.player and row.player not in self._players:
            self._players.append(row.player)
        if row.event and row.event not in self._event_types:
            self._event_types.append(row.event)
        if self._passes_filters(row):
            self._show_row(row)

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

    def _show_row(self, row: LogRow) -> None:
        """Add *row*, collapsing a world_response into its pending request.

        Collapse is disabled under turn focus, which wants the full,
        uncollapsed llm_call -> action -> request -> response -> mission chain.
        A response with no pending request (e.g. attached mid-run) or a request
        whose response is filtered out falls through and shows on its own line.
        """
        key = self._round_trip_key(row)
        if self._focus_key is None and row.event == "world_response" and key is not None:
            pending_index = self._pending_round_trips.pop(key, None)
            if pending_index is not None:
                self._collapse_response(pending_index, row)
                return
        self._append_table_row(row)
        if self._focus_key is None and row.event == "world_request" and key is not None:
            self._pending_round_trips[key] = len(self._displayed_rows) - 1

    def _collapse_response(self, index: int, response: LogRow) -> None:
        """Fold *response* into the already-displayed request row at *index*."""
        request = self._displayed_rows[index]
        table = self.query_one(DataTable)
        table.update_cell_at(
            Coordinate(index, COLUMNS.index("detail")),
            _round_trip_detail(request, response),
        )

    def _append_table_row(self, row: LogRow) -> None:
        table = self.query_one(DataTable)
        event_text = Text(row.event or "", style=EVENT_COLORS.get(row.event or "", "white"))
        table.add_row(
            row.time.strftime("%H:%M:%S.%f")[:-3],
            row.player or "-",
            row.turn if row.turn is not None else "-",
            event_text,
            _detail(row),
        )
        self._displayed_rows.append(row)
        if self._follow:
            table.move_cursor(row=table.row_count - 1)

    def _rerender_table(self) -> None:
        """Rebuild the table from scratch after a filter change."""
        table = self.query_one(DataTable)
        table.clear()
        self._displayed_rows = []
        self._pending_round_trips = {}
        for row in self._rows:
            if self._passes_filters(row):
                self._show_row(row)

    # -- actions ------------------------------------------------------

    def action_cycle_player_filter(self) -> None:
        """Cycle the player filter through: all -> each known player -> all."""
        self._focus_key = None
        options: list[str | None] = [None, *sorted(self._players)]
        idx = options.index(self._player_filter) if self._player_filter in options else 0
        self._player_filter = options[(idx + 1) % len(options)]
        self._rerender_table()

    def action_cycle_event_filter(self) -> None:
        """Cycle the event-type filter through: all -> each known event type -> all."""
        self._focus_key = None
        options: list[str | None] = [None, *sorted(self._event_types)]
        idx = options.index(self._event_filter) if self._event_filter in options else 0
        self._event_filter = options[(idx + 1) % len(options)]
        self._rerender_table()

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
        self._rerender_table()

    def action_clear_filters(self) -> None:
        """Drop the player filter, event filter, and turn focus."""
        self._player_filter = None
        self._event_filter = None
        self._focus_key = None
        self._rerender_table()

    def action_toggle_follow(self) -> None:
        """Toggle whether new rows auto-scroll the cursor to the bottom."""
        self._follow = not self._follow


def main() -> None:
    """Entry point for `make tui` / `python -m laife.observability.tui`."""
    ObservabilityApp().run()


if __name__ == "__main__":
    main()
