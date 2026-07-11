---
status: planned
---

# Phase 1 - survive error responses

## Overview

`Player._world_request` (`src/laife/entities/player.py:317`) raises `TypeError`
on any response that is not the expected type, treating a mismatch as a world
implementation bug. But `WResError` is a legitimate, typed response
(`route_interaction -> WResInteract | WResError`), so one bad LLM target pick
kills the whole `asyncio.gather` in `game/main.py`. Make the error a survivable
turn outcome. Context: [`00_start.md`](00_start.md).

## Goals

1. A `WResError` reply to any request ends that turn gracefully:
   the player logs it, records it in history so the brain sees the failure,
   and continues to the next turn.
2. A genuinely wrong response type (neither the expected type nor `WResError`)
   still fails loudly - that contract stays.

## Plan

- Decide the seam (open question in `00_start.md`): either `_world_request`
  returns `T | WResError` and every call site handles it, or the error is caught
  once in `Player.play()` around the action dispatch. Prefer the single seam in
  `play()` if call sites do not need per-kind error handling.
- Feed the error message into the player's history/observation so the next
  action pick knows the interaction failed and why.
- Emit the failure on the struct log (the existing `world_response` event already
  carries `status`; verify an error status renders usefully in the TUI).
- Regression test: an interact against a nonexistent target completes the turn
  and the player keeps playing; a wrong-type response still raises.

## Out of scope

- Why the LLM picked a building (phase 2).
- Retry policies or backoff on failed requests.

## Done when

- Reproducing the captured incident (interact with a building name) no longer
  ends the game; the failure is visible in the struct log and in history.
- Project verification suite passes
  (`uv run pytest && uv run ruff check . && uv run pyright`).
