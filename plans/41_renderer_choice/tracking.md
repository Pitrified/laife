# renderer choice - implementation tracking

Which frontend shows the world, and the protocol between it and the game loop.
Assessment, options and open questions in [`00_start.md`](00_start.md).

## Key decisions

- A web app replaces pygame: FastAPI in the game's asyncio loop, snapshot, SSE and POST; plain ES modules, Canvas 2D world, HTML panels. Details in `00_start.md`, Decisions 2026-11-14.
- The protocol is built first and kept cheap to change: one module of models and a contract test, no versioning.

## Phases

| # | Phase | Plan | Status |
| - | ----- | ---- | ------ |
| 1 | world protocol, no client | [`01_world_protocol.md`](01_world_protocol.md) | done |
| 2 | clean stop, and a quit route | [`02_clean_stop.md`](02_clean_stop.md) | done |
| 3 | page skeleton | [`03_page_skeleton.md`](03_page_skeleton.md) | done |
| 4 | PixiJS, zoom and pan, the player detail | [`04_pixi_detail.md`](04_pixi_detail.md) | done |
| 5 | retire pygame | [`05_retire_pygame.md`](05_retire_pygame.md) | in progress |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-11-13 : bootstrapped from the `plan.md` item "Renderer: pygame or a web app" with the user's pros and cons; assessed pygame, pygame-ce, a web app, Python web frameworks, Arcade and other Python libraries, Godot, Flutter, Unity and others; split the question into the protocol and the client; provisional phases and Q1-Q9.
- 2026-11-14 : Q1-Q9 answered and folded in: web app, protocol first and not frozen, Canvas 2D with the existing player PNGs, FastAPI, plain ES modules, pygame retired, localhost by default, TUI stays. The 3.14 pin stays: the problem was pygame's missing wheel, not the pin. Next: phase 1's sub-plan.
- 2026-11-14 : phase 1 sub-plan written: `src/laife/web/` with snapshot, event hub fed by a loguru sink sharing `LogRow`'s shape, FastAPI app, uvicorn as a task; `make headless SERVE=1`. Review against the code: `Mission.parent_mission` makes a mission view necessary; uvicorn 0.54 re-raises the captured signal after shutdown; httpx's ASGI transport cannot read an endless stream, so the stream test uses a real socket. Q10-Q12 open.
- 2026-11-14 : Q10-Q12 answered: `--pace` and `--paused`, fastapi and uvicorn approved as dependencies with unattended runs allowed, port 8002. The separate mission view is dropped: `Field(exclude=True)` on `parent_mission` dumps the whole tree (tried on a subclass; the current model raises `Circular reference detected`). Phase 1 planned.
- 2026-11-14 : phase 1 started; review against the code found nothing new beyond the planning review.
- 2026-11-14 : phase 1 done (7623bef): `laife.web` with snapshot, event hub and sink, FastAPI routes; `make headless SERVE=1` with `PACE`, `PAUSED`, `HOST`, `PORT`; `Mission.parent_mission` excluded from dumps; fastapi and uvicorn added. `make check` passes, 289 tests; plain `make headless` unchanged. On g7: `/state` answers, 78 events streamed in 3 s at pace 0.2, pause holds `seq` and turns still, step moves one player one turn, Ctrl-C prints `stopped` with no traceback. Closing review: `_cancel` re-raised done tasks in `finally`, fixed before the commit. Findings for phase 2 and the backlog in the phase file.
- 2026-11-14 : defect in phase 1: with a client on `/events`, Ctrl-C does not stop a serving run; on g7 the game played on 40 s after SIGINT and exited only when `curl` hung up, since uvicorn waits for open responses and a stream never ends. New phase 2 (clean stop, with the user's question of a quit route assessed in it); the page and later phases move to 3-5. Backlog: save and resume a world, the build/craft completing the root mission, the history reset.
- 2026-11-14 : Q13 answered a: the quit route comes with the stop fix. Phase 2 planned and started.
- 2026-11-14 : phase 2 done (940dd49): `EventHub.close()`, one stop path for Ctrl-C (a `uvicorn.Server` subclass) and `POST /control/quit`, `timeout_graceful_shutdown` 3 s. Tests shown failing first: all four new ones on the phase 1 code, and the subprocess `quit` case on the script that printed `stopped` only for Ctrl-C. `make check` passes, 295 tests. On g7 with `curl -N` on `/events`: Ctrl-C and quit each exit within 2 s, the stream closes, `stopped`, no traceback; plain `make headless` unchanged.
- 2026-11-14 : phase 3 sub-plan written: `ui/world_web/` served by FastAPI, Canvas 2D world, player cards with latest actions from the stream, snapshot refetched on events (at most every 250 ms), pause, step, resume, quit; `/sprites` from a pygame-free sprite table; Playwright test with a screenshot. Checked: playwright 1.63 matches g7's Chromium 1243; positions are pixels, players centred and the rest top-left, as pygame draws them. Q14-Q16 open.
- 2026-11-14 : Q14-Q16 answered as recommended: view fits the snapshot and only grows, `make e2e` outside `make check`, playwright approved with no JS linter yet. Phase 3 planned and started.
- 2026-11-14 : phase 3 implemented (6f88a13): `ui/world_web/` page, `/sprites` and static mounts, `laife.config.sprites` without pygame, `make e2e` with Playwright and a screenshot in `cache/e2e/`. `make check` passes, 299 tests and the browser test deselected; `make e2e` passes in about 5 s and fails with the step button disconnected; plain `make headless` unchanged. Waiting on the user's check on g4 before the phase closes.
- 2026-11-14 : phase 3 done: the user checked the page on g4 through an SSH tunnel to a serving run on g7; the run moved, and pause, step, resume and quit all worked.
- 2026-11-14 : after a quit from the page on g4, the SSH tunnel logged a refused connection: the page reconnected to the server it had just stopped. Harmless; the fix (close the stream before sending quit) goes into phase 4's sub-plan.
- 2026-11-14 : assessed the move to PixiJS for the user (the drawing is a contained rewrite; serving a library is the bigger, one-time part). The user chose PixiJS now with clean vendoring, and a detail view showing one player with its whole mission tree. Phase 4 sub-plan written; pins pixi.js 8.22.0 and pixi-viewport 6.0.3, since 8.23.0 and the 7.x line are under two weeks old. Q17-Q20 open.
- 2026-11-14 : Q17-Q20 answered as recommended: trimmed vendoring copy with a backlog note, stream actions only, centre once on select, Pillow for the canvas check. Phase 4 planned and started.
- 2026-11-14 : phase 4 implemented (39825cc): `ui/vendor.toml` with pixi.js 8.22.0 and pixi-viewport 6.0.3, `laife.web.vendor` and `make vendor`, `/vendor` route checking the lock; world on PixiJS with drag, wheel, pinch, fit and sliding moves; detail view with the whole mission tree, inventory and 30 actions, centring on select; quit closes the stream first. `make check` passes, 308 tests, no network; `make e2e` passes in about 11 s, its quit check shown failing with the fix removed. Backlog: vendoring shared with abyss. Waiting on the user's check on g4.
- 2026-11-14 : phase 4 done: the user checked the page on the phone over Tailscale, served on g7's tailnet address (log `game_20261114T095327.jsonl`): pause, pinch zoom, selecting a player and its detail, quit; the run ended cleanly.
- 2026-11-14 : phase 5 sub-plan written: `serve_run` shared by `make run` and the headless serve, the live game on the page with a turn cap, `quit` and `stopped` log events, pygame and `src/laife/rendering/` removed, folder 34 phases 1 and 3 discarded. Live check on g4 at most 24 calls for 2 players and 3 turns. Q21-Q24 open.
- 2026-11-14 : Q21-Q24 answered as recommended: `LIVE_TURNS` default 3, `make run` starts paused, `--seed` folded in, localhost by default. Phase 5 planned and started.
- 2026-11-14 : phase 5 implemented (8558c83): `laife.web.run.serve_run` shared by `make run` and the headless serve; `game/main.py` serves the live world, paused, `LIVE_TURNS` 3, `--seed`; `quit` and `stopped` log events; pygame and `src/laife/rendering/` removed with their docs; folder 34 done. `make check` 309 tests, `make e2e` and plain `make headless` pass with pygame uninstalled; no pygame mention left outside `plans/`, `scratch_space/` and the lock. Waiting on the user's live check on g4.
