---
status: done
---

# Phase 2 - textual tui inspector

## Overview

Build the decoupled inspector as a Textual TUI: a separate process that tails
the `.jsonl` struct log and renders it with tables, filtering, and scrollback.
Decoupled from the game loop, no graphics stack. Depends on the catalogue from
[`01_struct_log_analysis.md`](01_struct_log_analysis.md). Context:
[`00-start.md`](00-start.md).

Why Textual (not pygame/pygame_gui/web): best effort-to-payoff for a
developer-facing inspector - tables, filtering, scrollback, and key bindings
nearly free, fully decoupled, reads the existing `.jsonl` directly. Pygame stays
out of the observability path.

## Goals

1. A Textual app that tails `cache/game_*.jsonl` live and shows each record.
2. Filtering on the axes from phase 1: event type, player, status.
3. A readable layout that does not drop events while the sim runs.

## Plan

Superseded by the detailed plan below (phase 1 landed with `(player, turn)` on
every event, `world_request` fixed to `INFO`, and `world_response` now emitted
for all six request kinds - this plan reflects that, not the phase-1 draft).

- New dependency-group `tui = ["textual>=0.60"]` in `pyproject.toml`
  (alongside `docs`/`lint`/`notebook`/`test`, folded into `dev` like the
  others), plus a `make tui` target (`uv run python -m
  laife.observability.tui`) in the `Makefile`.
- New subpackage `src/laife/observability/`:
  - `log_reader.py` - a pure, testable piece with no Textual dependency.
    An async generator `tail_jsonl(path) -> AsyncIterator[LogRow]` that:
    1. Opens the file, reads whatever is already there (so a TUI attached
       mid-run sees history, not just new lines), then keeps polling for
       appended lines (plain polling loop with a short `asyncio.sleep`,
       since `configure_logging(enqueue=True)` writes from a background
       thread on a bare file, not a pipe).
    2. Parses each line as JSON (loguru's `serialize=True` format: a
       `{"text": ..., "record": {...}}` envelope) and extracts exactly the
       fields phase 1 catalogued: `record.time`, `record.level.name`,
       `record.message`, and everything under `record.extra` (`event`,
       `player`, `turn`, and the event-specific fields: `action`, `kind`,
       `status`, `to_status`, `model`, `elapsed`).
    3. Yields a small `LogRow` (`@dataclass`, no pydantic needed - this is a
       read-only display value, not a validated payload) per line; skips/
       logs malformed lines instead of crashing the tail.
    - Locate the target file by default: newest `cache/game_*.jsonl` by
      mtime (`sorted(Path("cache").glob("game_*.jsonl"))[-1]`); accept an
      optional path argument to point at an older run.
  - `tui.py` - the Textual `App`. A single `DataTable` (columns: time,
    player, turn, event, detail - `detail` is a per-event-type summary built
    from the row's extras, e.g. `status=success` for `world_response`,
    `to_status=completed` for `mission_transition`). A background `@work`
    task drains `tail_jsonl()` into the table via an `asyncio.Queue` so file
    I/O never blocks the UI. `BINDINGS` for: cycle player filter, cycle
    event-type filter, toggle follow-tail/paused, and the flagship feature
    phase 1's correlation work unlocks - press a key on a row to filter down
    to just that row's `(player, turn)`, showing one full turn's
    `llm_call -> action -> world_request -> world_response ->
    mission_transition` chain together. `Footer` widget shows the active
    bindings.
- Color/severity cues by event type so action/response/mission/llm read at a
  glance.
- Keep it read-only; pause/step controls are phase 3, but leave a
  footer/region reserved for them.

## Out of scope

- Pause/step controls (phase 3).
- Web UI, timelines, replay - deferred; revisit only if the TUI proves limiting.
- Spatial/world-map rendering.
- Writing back to the game - the TUI only ever reads the `.jsonl`.

## Testing

- `log_reader.tail_jsonl` is a plain async generator - unit-test it against a
  small fixture `.jsonl` file written by the test (assert the parsed
  `LogRow`s, and that a line appended mid-iteration is picked up).
- Textual ships `App.run_test()` (a headless "pilot") for testing key
  bindings and filter state without a real terminal - use it for the
  App-level tests instead of hand-rolling terminal mocks.
- Manual smoke: run the game briefly to produce a real `cache/game_*.jsonl`,
  then run `make tui` against it and confirm live rows appear and the
  `(player, turn)` focus filter groups a build/craft turn correctly (the
  same chain verified manually while landing phase 1).

## Done when

- Running the TUI against a live `.jsonl` shows events as they are written.
- Event-type, player, status, and `(player, turn)`-focus filtering all work.
- No events are dropped or crash the view during a normal game run.
- `log_reader.tail_jsonl` has unit test coverage independent of Textual.

## Outcome

Built as planned, with one narrowing on "status" filtering: player and
event-type filters both landed as designed, but a dedicated *status* filter
was dropped - `status` only exists on `world_response` rows, and the
`(player, turn)`-focus feature already isolates a turn's full chain (which
includes its response's status) more usefully than a global status filter
would. Can be added later if it turns out to be missed.

- `pyproject.toml`: new `tui` dependency-group (`textual>=0.60`), folded
  into `dev`. `Makefile`: `make tui` target.
- `src/laife/observability/log_reader.py`: `LogRow` dataclass and
  `tail_jsonl(path) -> AsyncIterator[LogRow]`, reading existing content then
  polling for appends (plain blocking file I/O in a poll loop, not a fully
  async file API - the writer appends from a background thread onto a bare
  file, so there's nothing to actually `await` on). Skips malformed/partial
  lines instead of crashing. `latest_log_file()` picks the newest
  `cache/game_*.jsonl` by filename (timestamps sort lexicographically).
  Pure - no Textual import - and unit-tested against fixture `.jsonl` files,
  including a line appended mid-iteration.
- `src/laife/observability/tui.py`: `ObservabilityApp`, a single `DataTable`
  (time, player, turn, event, detail - `detail` is a per-event-type summary
  built from `LogRow.extra`) colored by event type. A `_read_log` worker
  tails the file and pushes rows onto an `asyncio.Queue`; a `_drain_queue`
  worker consumes the queue and applies rows to the table, so file polling
  never touches the render path. `BINDINGS`: `p`/`e` cycle the player/event
  filters, `t` focuses the `(player, turn)` of the selected row (the
  correlation-tracking payoff from phase 1 - one keypress shows a full
  `llm_call -> action -> world_request -> world_response ->
  mission_transition` chain), `c` clears all filters, `f` toggles
  follow-tail auto-scroll.
- Tests: `tests/observability/test_log_reader.py` (plain async-generator
  unit tests) and `tests/observability/test_tui.py` (Textual's headless
  `App.run_test()` pilot - loads existing rows, cycles the player filter,
  clears filters, and verifies focus-turn narrows to one `(player, turn)`).
  10 new tests, all passing.
- Manual smoke: wrote a real `cache/game_*.jsonl` covering one full turn's
  five-event chain across two players, ran the app headless against it -
  all 6 rows loaded and rendered correctly, focus-turn narrowed to the
  5-event Alice/turn-1 chain, clear restored all 6, player filter narrowed
  to Alice's 5 rows. File removed after the check (not a real run).
- Full suite: 195 tests passing, `ruff check .` and `pyright` both clean
  (the two `scratch_space/` `I001` warnings predate this work and are
  unrelated).
