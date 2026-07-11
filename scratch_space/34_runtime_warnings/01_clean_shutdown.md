---
status: draft
---

# Phase 1 - clean shutdown on quit

## Overview

Quitting the game window ends with
`Task exception was never retrieved ... exception=SystemExit()` because
`WorldRenderer.quit()` (`src/laife/rendering/world_renderer.py:128`) calls
`sys.exit()` from inside a coroutine gathered in `game/main.py::main`.
Replace the in-task `sys.exit()` with a cooperative shutdown.
Context: [`00_start.md`](00_start.md).

## Goals

1. Quitting via the window close button or `q` ends the process with no
   unretrieved-exception report and exit code 0.

## Plan

- Decide the mechanism: raise a dedicated `GameQuit` exception caught in `main()`,
  or cancel the sibling tasks via a shared `asyncio.Event` / `gather` cancellation.
  Prefer whichever leaves `WorldRenderer` free of process-control responsibility.
- `renderer.quit()` keeps `pygame.quit()` but stops calling `sys.exit()`.
- Player tasks and `runner.simulate()` must unwind promptly
  (they block on queues and on `SimControl`; cancellation is the likely path).
- Regression coverage: a test that drives the quit path headless
  (`SDL_VIDEODRIVER=dummy`, posted `QUIT` event) and asserts clean task teardown.

## Out of scope

- Persisting game state on exit.

## Done when

- `make run` then quit shows no `Task exception was never retrieved` line.
- Project verification suite passes
  (`uv run pytest && uv run ruff check . && uv run pyright`).
