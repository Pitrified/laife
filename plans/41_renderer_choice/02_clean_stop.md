---
status: in progress
---

# Phase 2 - Clean stop, and a quit route

## Overview

A defect in phase 1, found on 2026-11-14 after it closed: while any client holds `/events` open, Ctrl-C does not stop a serving run.
uvicorn's shutdown waits for open responses to finish, and an event stream never finishes.
On g7, with `curl -N` on `/events`, the game kept playing for 40 s after SIGINT (events to `seq` 508) and the process exited only when `curl` hung up.
The page in phase 3 always holds a stream, so every stop would hang.

The same work answers the user's question whether the page should be able to stop the run, `POST /control/quit`.
Context: [`00_start.md`](00_start.md), [`01_world_protocol.md`](01_world_protocol.md).

## Assessment of a quit route

Useful, for these reasons:

- **Stopping a live run from where you watch it.** Phase 5 makes `make run` serve the page instead of opening a window, so the window's close button and `q` go away. A live run spends credit, and a run started on g7 and watched from g4 or the phone could otherwise only be stopped from a terminal on g7.
- **Agents stop a run by `curl`,** not by finding a pid.
- **One shutdown path.** The route and Ctrl-C end the same way, and it replaces the `sys.exit()` inside a task that folder 34 phase 1 wanted gone.

Limits:

- Pause already stops new LLM calls (a turn in flight finishes), so quit is not the only way to stop spending; it ends the process, frees the port and closes the log.
- The page cannot start a run again: after quit it shows that the server is gone. Restarting stays a terminal action, or a supervisor later.
- Anyone who can reach the page can stop the run. The pause routes already have that trust, and the server binds localhost unless told otherwise.

## Plan

- `EventHub.close()`: ends every subscriber's stream (each gets `None`) and turns away new subscribers with the stream ending at once.
- One stop path, `stop()`: `hub.close()`, then `server.should_exit = True`. uvicorn then finishes the requests in flight, the quit response included, and `serve()` returns.
- Ctrl-C goes through it: a `uvicorn.Server` subclass whose `handle_exit` calls `hub.close()` before uvicorn's own handling. Belt and braces: `timeout_graceful_shutdown` set to a few seconds, so a connection the hub does not own cannot hold the process.
- `POST /control/quit`: answers `{"stopping": true}` and calls `stop()`. Available whether or not the run has a `SimControl`.
- `serve_headless` returns when the server's task ends, as now; quit therefore returns normally (no `KeyboardInterrupt`), and `game/headless.py` prints `stopped` for both.

## Tests

- Over a real socket, with a stream open: `POST /control/quit` returns, the stream ends, `serve_headless` returns. Shown hanging (failing on a timeout) before the fix.
- Ctrl-C with a stream open: a test sends SIGINT to the process running `game/headless.py --serve`, with a client on `/events`, and checks the exit within a few seconds. Shown failing before the fix.
- `EventHub.close()`: open subscriptions get `None`; a subscription made after close ends at once.

## Out of scope

- Restarting a run from the page.
- The live game's stop: phase 5 uses this path when `make run` serves.

## Done when

- `make check` passes.
- On g7 with `curl -N` on `/events`: Ctrl-C exits within a few seconds, and so does `curl -X POST /control/quit`, both printing `stopped`, no traceback.

## Open questions

- Q13: Add `POST /control/quit` as assessed above?
  - a. Yes, with the stop fix in this phase.
  - b. Only the stop fix; quit later or never.
  - Recommended: a, because the fix builds the stop path anyway and the route is one call into it; its real use comes with the live game in phase 5.
  - ANS: a.
