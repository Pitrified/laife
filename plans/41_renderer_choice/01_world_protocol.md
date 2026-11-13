---
status: planned
---

# Phase 1 - World protocol, no client

## Overview

A view outside the Python process needs three things from the game: the world as it is now, what happens next, and a way to pause, resume and step.
This phase serves them over HTTP from the game's own asyncio loop, with no page yet, and gives the headless run a mode that keeps serving so the page in phase 2 can be built against it without a provider.
Context: [`00_start.md`](00_start.md), Decisions 2026-11-14.

The protocol is meant to change as the page needs it (`00_start.md` Q1): one module of models, no versions, no compatibility shims.

## Goals

1. `GET /state` returns a snapshot of the world as JSON.
2. `GET /events` streams world events as Server-Sent Events, in the same shape `make tui` reads from the log.
3. `POST /control/pause`, `/control/resume`, `/control/step` drive `SimControl`.
4. `make headless SERVE=1` runs the scripted world with the server up, and keeps serving after the players finish.
5. Everything above is checked by tests and by an agent on g7 with `curl`.

## Plan

### Layout

A new package `src/laife/web/`, with no pygame import, beside `entities/` and `observability/`:

- `snapshot.py`: the view models and the function that builds one from a runner.
- `events.py`: the event hub and the loguru sink that feeds it.
- `server.py`: the FastAPI app factory and the coroutine that serves it.

Tests in `tests/web/`, mirroring it.

### Snapshot

- `WorldSnapshot`: `seq` (the last event number, see below), `paused` (`None` when there is no `SimControl`), `terrains`, `buildings`, `players`.
- `Terrain` and `Building` are pydantic models already and go in as they are.
- `PlayerView`, built from a `Player`: name, `player_type`, position, size, state, turn, mission, inventory (name and description per utensil), and the last few entries of `history` (action and result) for the "latest actions" list.
- The mission goes in as `Mission` itself. Its `parent_mission` points back up the tree, and pydantic refuses the dump today with `Circular reference detected (id repeated)`.
  The data model change this phase makes: `parent_mission` gets `Field(default=None, exclude=True)`. Excluding a field on the model applies at every level of the tree, so the steps nest and no parent link is written (tried 2026-11-14 on a subclass: the whole tree dumps).
  Nothing in `src` or `tests` dumps a mission or reads `parent_mission` outside `mission.py`, so the exclusion changes no current behaviour. The schema FastAPI publishes for responses uses pydantic's serialization mode, which leaves the field out too.
- `snapshot(runner, sim_control) -> WorldSnapshot` is a plain function: the server calls it, and a test calls it on a headless runner with no HTTP at all.
- How many history entries the view carries is a constant in `snapshot.py`, small (5 to 10); the detail card in phase 3 may ask for more.

### Events

- The source is the structured log: a second loguru sink, a function, added beside the file sink. Every `slog` record becomes an event, so the page, the TUI and the file cannot disagree.
- The event shape is `LogRow`'s fields (`time`, `level`, `message`, `event`, `player`, `turn`, `extra`) plus `seq`, a counter per run. The record-to-row conversion in `log_reader._parse_line` is split out and shared by the file parser and the sink, so there is one conversion, and replaying a `.jsonl` later produces the same events.
- `EventHub`: subscribers each get a bounded `asyncio.Queue`; `publish` puts to each without awaiting. A subscriber whose queue is full is dropped, and its stream ends; the page reconnects and refetches `/state`. Ceiling: a slow tab loses its stream rather than slowing the game, which is the right trade for a view.
- The sink runs in the thread that logs. Records logged on the loop's thread publish directly; any other thread goes through `loop.call_soon_threadsafe`. Which threads log today is checked during implementation rather than assumed.
- `seq` lines up the snapshot with the stream: the page fetches `/state`, opens `/events`, and drops events with `seq` at or below the snapshot's. Each SSE message carries `id: <seq>`.

### Endpoints

- `GET /state`: `snapshot(...)`, `response_model=WorldSnapshot`.
- `GET /events`: a `StreamingResponse` of `text/event-stream`, one `data:` line of JSON per event, and a comment line as a heartbeat every 15 s so proxies and the browser keep the connection.
  `sse-starlette` is the alternative if the hand-written stream needs more than a few lines.
- `POST /control/pause`, `/resume`, `/step`: call `SimControl`, return the new `paused` value; `409` with a message when the run has no `SimControl`.
- `GET /openapi.json` comes from FastAPI and is the contract the page's test reads in phase 2.
- `create_app(runner, sim_control, hub) -> FastAPI`: no global state, so tests build their own.

### Serving inside the game loop

- `serve(app, host, port)` runs `uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_config=None)).serve()` as one more task beside the world and the players.
- uvicorn swaps in its own SIGINT and SIGTERM handlers while it serves (`Server.capture_signals`), shuts down on the first signal, and then re-raises it with `signal.raise_signal` once `serve()` returns (read in the installed uvicorn 0.54). So Ctrl-C ends the server's task cleanly and then arrives as a `KeyboardInterrupt` in `asyncio.run`.
  The run cancels the world and the players when the server's task ends, and `game/headless.py` catches the `KeyboardInterrupt` around `asyncio.run` to exit without a traceback. Folder 34 phase 1 wanted the same clean exit for the window.
- Host `127.0.0.1` by default, `--host` to bind the tailnet address. Port 8002 by default, abyss uses 8001.

### Headless with the server

- `game/headless.py` gains `--serve`, `--host`, `--port`; the Makefile passes them from `SERVE`, `HOST`, `PORT`, as it does `TURNS` and `SEED`. One entry point, which `00_start.md` Q8 left to this plan.
- With `--serve`, the run builds a `SimControl` (the plain headless run passes `None`), starts the server, and keeps serving after the players finish, until Ctrl-C. `--turns 0` means no limit, `play(max_turns=None)`.
- Without `--serve` nothing changes: `make headless` stays the quick gate.
- Pacing (Q10): the scripted model answers at once, so an unpaced endless run floods the log.
  `--pace SECONDS` delays each scripted answer, default 1 when serving and 0 otherwise; the delay is an awaited `asyncio.sleep`, so it holds the calling player and nothing else.
  `--paused` starts the `SimControl` paused, for tests and screenshots that step the world by hand.
  The Makefile passes `PACE` and `PAUSED` like the other options.

### Docs

- `docs/guides/web.md`: the endpoints, the event shape, `seq`, and how to run it; linked in `mkdocs.yml` beside the headless guide.
- `docs/guides/headless.md`: the `SERVE` option.
- `.github/copilot-instructions.md`: a row for `src/laife/web/` in the layer table, and `make headless SERVE=1` under "Running the engine".

### Tests

- `snapshot()` on a headless runner after a few turns: players, mission tree, history, and that the result dumps to JSON.
- A mission with two levels of sub-missions dumps to JSON with its steps nested and no `parent_mission`; the test fails on the current model.
- `EventHub`: publish to two subscribers, a full queue drops its subscriber, `seq` grows by one.
- The sink: an `slog` record arrives as an event with the same fields `_parse_line` gives for the same record in the file.
- The app with httpx's `ASGITransport`: `/state` and the three control endpoints, including the `409`.
- The stream: httpx's ASGI transport waits for the whole response, so it cannot read an endless stream. One test serves on `127.0.0.1` port 0 in the test's loop, runs a two-turn headless game, and reads events over a real connection until it sees an `action`.

## Out of scope

- Any page, JavaScript or vendored file (phase 2).
- The live game: `game/main.py` and pygame do not change until phase 4.
- Replay from a `.jsonl` file: the shared event shape makes it possible, a later folder builds it.
- Authentication.

## Done when

- `make check` passes, with the new tests counted.
- `make headless` behaves as before.
- `make headless SERVE=1 TURNS=0` on g7: `curl` on `/state` returns players and missions; `curl -N` on `/events` shows events arriving; `POST /control/pause` holds the turns and `/control/step` releases one, visible in the stream.
- Ctrl-C ends the run without a traceback.

## Open questions

Continuing the numbering of [`00_start.md`](00_start.md); answers go here.

- Q10: How an endless serving run is paced.
  - a. A delay per scripted answer, `--pace SECONDS`, default 1 when serving; the run looks like a slow model and the world is untouched.
    llm-core's `ScriptedChatModel.with_structured_output` returns a sync `RunnableLambda`; `RunnableLambda` also takes an `afunc`, so an async answer that awaits `asyncio.sleep` is possible. Whether that is a `delay` field on llm-core's model (a release and a pin bump) or an override in laife's `ScriptedChatConfig` is settled when the code is read; laife's side first.
  - b. The serving run starts paused; the page or `curl` steps it. Fully deterministic, which suits tests, but nothing moves until someone presses a button.
  - c. A minimum turn interval in `SimControl`. It touches the live game's gate for a development need.
  - Recommended: a, plus b as a flag (`--paused`) for tests and screenshots; c changes engine code for a dev convenience.
  - ANS: a, plus `--paused` for tests and screenshots.
- Q11: The dependency: `fastapi` and `uvicorn` become direct dependencies of laife (uvicorn is in the lock already, through chromadb). The repo rule is that a phase adding a dependency does not run unattended.
  - a. Approved here; the phase may run unattended once planned.
  - b. Approved, but the phase runs with the user watching.
  - Recommended: a, since the user said dependencies are not a concern and the rest of the phase is checkable headless.
  - ANS: a, approved; the phase may run unattended once planned.
- Q12: The default port. abyss serves on 8001.
  - a. 8002.
  - b. Another port the user already keeps free on g7.
  - Recommended: a; on g7, 8000 and 8001 are listening on localhost and 8002 is free (checked 2026-11-14).
  - ANS: a, 8002.
