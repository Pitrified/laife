# renderer choice - implementation tracking

Which frontend shows the world, and the protocol between it and the game loop.
Assessment, options and open questions in [`00_start.md`](00_start.md).

## Key decisions

- A web app replaces pygame: FastAPI in the game's asyncio loop, snapshot, SSE and POST; plain ES modules, Canvas 2D world, HTML panels. Details in `00_start.md`, Decisions 2026-11-14.
- The protocol is built first and kept cheap to change: one module of models and a contract test, no versioning.

## Phases

| # | Phase | Plan | Status |
| - | ----- | ---- | ------ |
| 1 | world protocol, no client | not written | draft |
| 2 | page skeleton | not written | draft |
| 3 | player detail and zoom | not written | draft |
| 4 | retire pygame | not written | draft |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-11-13 : bootstrapped from the `plan.md` item "Renderer: pygame or a web app" with the user's pros and cons; assessed pygame, pygame-ce, a web app, Python web frameworks, Arcade and other Python libraries, Godot, Flutter, Unity and others; split the question into the protocol and the client; provisional phases and Q1-Q9.
- 2026-11-14 : Q1-Q9 answered and folded in: web app, protocol first and not frozen, Canvas 2D with the existing player PNGs, FastAPI, plain ES modules, pygame retired, localhost by default, TUI stays. The 3.14 pin stays: the problem was pygame's missing wheel, not the pin. Next: phase 1's sub-plan.
