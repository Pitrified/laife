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

## Decisions

- **Seam: widen `_world_request` to return `T | WResError`** rather than
  catching in `play()`. Grounds for the choice, from reading `play()`:
  - the dispatch already funnels every branch into a single
    `wrsp` -> `MissionHistoryEntry(action=action, result=str(wrsp))`, so an
    error response flows into history with zero extra plumbing;
    `WResError.__repr__` already renders status and message.
  - `_update_mission_from_response` guards with
    `isinstance(wrsp, WResBuild)` / `WResCraft`, so a `WResError` passes
    through as neutral - no mission state corruption.
  - catching in `play()` would need the raise to survive the helper methods
    (`move`, `interact`, ...) whose post-request code (`alg.log`,
    caching `last_observation`) must not run on an error anyway;
    the type-widening forces each helper to short-circuit explicitly,
    which is the honest control flow.
- The fail-loudly contract stays for genuinely unknown types: anything that is
  neither `response_type` nor `WResError` still raises `TypeError`.
- `observe()` is special: it caches `last_observation` and its callers assume
  a fresh observation exists. On `WResError` it keeps the previous observation
  and logs the failure; first-turn observe failure is a world bug and may
  still fail loudly (there is nothing cached to fall back to).

## Goals

1. A `WResError` reply to any request ends that turn gracefully:
   the player logs it, records it in history so the brain sees the failure,
   and continues to the next turn.
2. A genuinely wrong response type (neither the expected type nor `WResError`)
   still fails loudly.

## Plan

- `_world_request[T](...) -> T | WResError`: accept `WResError` as a valid
  response, keep the `TypeError` for anything else. The existing
  `EVT_WORLD_RESPONSE` struct-log bind already carries `kind` and `status`,
  so an error response logs as `kind=WResError status=error` with no new code.
- Widen the helper signatures that can receive routed errors
  (`interact` first - it is the reproduced case; then audit `move`, `build`,
  `craft`, `plan`, `complete`, `observe` against what `world_runner.simulate`
  can actually return for each kind) and short-circuit their post-processing
  on error.
- `play()`: the match arms already assign `wrsp`; verify the history entry and
  `_update_mission_from_response` behave on `WResError` (expected: yes, by
  design above) and add the turn-continues test.
- TUI check: confirm an error `world_response` row renders usefully
  (phase 4 of feature 32 collapses request/response pairs; the collapsed row
  shows `status`, which should read `error`).
- Regression tests, `tests/entities/`:
  - interact against a nonexistent target -> turn completes, history entry
    records the error, next turn starts (drive with a stub world queue, same
    pattern as `test_player_lifecycle.py`);
  - `_world_request` with an unrelated response type still raises `TypeError`;
  - `_update_mission_from_response` with `WResError` leaves mission status
    untouched.

## Out of scope

- Why the LLM picked a building (phase 2).
- Retry policies or backoff on failed requests.
- Feeding richer error context to the brain than the history line
  (revisit in phase 2 if the investigation wants it).

## Done when

- Reproducing the captured incident (interact with a building name) no longer
  ends the game; the failure is visible in the struct log and in history.
- Project verification suite passes
  (`uv run pytest && uv run ruff check . && uv run pyright`).
