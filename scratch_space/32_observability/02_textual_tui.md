---
status: planned
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

- Add `textual` as a dev/scratch dependency.
- Tail the log: open the newest `cache/game_*.jsonl` (or a path arg), follow
  appended lines (poll or watch), parse each JSON line into a record. Handle
  partial/last-line-not-yet-flushed reads gracefully (the sink is async/enqueued).
- Layout: a scrollable `DataTable` (or log view) with one row per event -
  columns `time`, `event`, `player`, `status`, and a details pane for the full
  payload of the selected row.
- Filtering: key bindings / input to filter by `event` type, `player`, and
  `status`. Default to showing `INFO`+; allow toggling `world_request` (DEBUG).
- Color/severity cues by event type so action/response/mission/llm read at a
  glance.
- Keep it read-only; pause/step controls are phase 3, but leave a footer/region
  reserved for them.

## Out of scope

- Pause/step controls (phase 3).
- Web UI, timelines, replay - deferred; revisit only if the TUI proves limiting.
- Spatial/world-map rendering.

## Done when

- Running the TUI against a live `.jsonl` shows events as they are written.
- Event-type, player, and status filtering work.
- No events are dropped or crash the view during a normal game run.
