# Serving the world

The game can serve its world over HTTP, so a client outside the Python process can show it and pause it.
The server runs as one more task in the game's asyncio loop, beside the world and the players, and reads the live objects directly.
The code is in [`laife.web`](../library/web.md).

Today only the headless run serves:

```bash
make headless SERVE=1                  # 6 turns per player, then keeps serving
make headless SERVE=1 TURNS=0          # no turn limit
make headless SERVE=1 PAUSED=1         # starts paused; step it by hand
make headless SERVE=1 PACE=0.2         # seconds per scripted answer, 1 by default
make headless SERVE=1 HOST=<tailnet address> PORT=8002
```

It listens on `127.0.0.1:8002` unless told otherwise, and stops on Ctrl-C or on `POST /control/quit`.
The scripted model answers instantly, so a serving run waits `PACE` seconds before each answer; without that an endless run fills the log in seconds.
The players finishing their turns does not stop the server: the final state stays readable.

## The page

`/` is the world page, from `ui/world_web/`: the world on the left, the players on the right, and pause or resume, step, fit and quit at the top.
From g4, with the run on g7: `ssh -L 8002:127.0.0.1:8002 g7`, then `http://localhost:8002`.

### The world

- Drawn by PixiJS, inside a `pixi-viewport`: drag to pan, wheel or pinch to zoom, between a little more than the whole world and 4x. Fit shows the whole world again.
- The snapshot is what is drawn. Each event makes the page fetch a fresh one, at most every 250 ms. A player whose position changed slides there over 200 ms; a long move jumps.
- The world's extent is everything the snapshot holds plus a margin, and only grows during a session, so fitting does not jump as players move.
- Players are drawn centred on their position, terrains and buildings from their top-left corner.
- The zoom is kept on the canvas as `data-zoom`, which the browser test reads.

### The panel

- With no player selected, a card per player: state, turn, mission, the active step, the latest three actions.
- A click on a card, or on a player in the world, shows that player alone and centres the view on it: position, the whole mission tree (the path to the active step highlighted, finished steps dimmed, failures counted), the inventory, and the last 30 actions. Back, or Escape, returns to the cards.
- Actions come from the `action` and `world_response` events, not from the snapshot's `history`, which resets on a new mission, a plan and a completed step. Observe responses are left out; repeated responses to one action, such as move steps, are counted. A page opened mid-run starts with an empty list.

### The connection

- When the stream drops, the page asks for `/state`; if the server is gone it says the run has ended and stops retrying.
- Quit closes the page's own stream first, so it does not reconnect to the server it is stopping.

### Third-party files

PixiJS and `pixi-viewport` are pinned in `ui/vendor.toml` by exact version and by the integrity hash npm publishes for each tarball.
`make vendor` downloads what is missing into `cache/vendor/` (not in git), refuses a tarball that does not match its pin, extracts only the listed files and records each file's sha256 in a lock beside it.
`/vendor/<package>/<file>` serves a file only if it is listed and still matches the lock; a page with an unfetched cache gets `404`s naming `make vendor`.
The page loads them through an import map in `index.html`, since `pixi-viewport` imports `"pixi.js"` by name; a unit test checks that every import map target is in the manifest.
A release is pinned once it has been out a few weeks. The scheme is abyss's, without its plain-file pins.

Otherwise the page is plain ES modules with no build step. Static files go out with `Cache-Control: no-cache`, so a reload shows an edit.

### Browser test

`make e2e` runs `make vendor`, then drives the page in headless Chromium against a paused run started as a separate process: the drawing, wheel zoom and fit, a step, a run and a pause, a player's detail, and a quit with no request after it. It saves `cache/e2e/world_page.png` with a detail open.
It is not part of `make check`; run it before committing a change to the page.
Playwright's Chromium lives in `~/.cache/ms-playwright`; on a machine without it, `uv run --no-sync playwright install chromium`.

## Routes

| Route | Answer |
| --- | --- |
| `GET /state` | the world now: terrains, buildings, players with position, state, turn, mission tree, inventory and latest history |
| `GET /events` | Server-Sent Events, one per structured log record |
| `POST /control/pause`, `/control/resume`, `/control/step` | `{"paused": bool}`; `409` when the run has no pause control |
| `POST /control/quit` | `{"stopping": true}`, then the server stops and the run with it |
| `GET /sprites` | the sprite URL for each player type and state |
| `/sprites/<type>/<file>`, `/` | the sprite images, and the page |
| `/vendor/<package>/<file>` | a third-party file from `ui/vendor.toml`, checked against its lock |
| `GET /openapi.json` | the schema of every route and model, from FastAPI |

```bash
curl -s http://127.0.0.1:8002/state
curl -sN http://127.0.0.1:8002/events
curl -s -X POST http://127.0.0.1:8002/control/step
```

## Stopping

Ctrl-C and the quit route stop the same way: the hub ends every open event stream, then uvicorn exits.
uvicorn waits for open responses before it stops, and an event stream never finishes by itself, so an open page would otherwise keep the run alive.
Any other connection gets a few seconds before uvicorn drops it.
The quit route makes the run return normally; Ctrl-C ends it with `KeyboardInterrupt`, which `game/headless.py` catches. Both print `stopped`.

The page cannot start a run again; that stays a terminal command.

## Events

Every record the structured log writes is also an event, with the same fields `make tui` reads from the file (`LogRow`: `time`, `level`, `message`, `event`, `player`, `turn`, `extra`) and a `seq` number.
The stream and the file come from one conversion, `parse_line` in `laife.observability.log_reader`, so they cannot disagree, and a log file read back gives the events a live run streamed.

Each message is `id: <seq>` and `data: <event as JSON>`.
When nothing happens for 15 seconds the server sends a comment line, which keeps the connection open through proxies.

## Snapshot and stream together

`seq` counts events from 1 in the order they were published.
A snapshot carries the `seq` of the last event published before it was taken.
A client fetches `/state`, opens `/events`, and drops events whose `seq` is at or below the snapshot's.

A client more than 1000 events behind is dropped: its stream ends, and it reconnects and fetches a fresh snapshot.
A slow tab then loses its stream instead of slowing the game.

## What the snapshot carries

- `history` is the player's history for its current mission, the latest few entries; it resets when a mission starts.
- A mission's sub-missions are nested in `steps`. The link from a sub-mission to its parent is not written, since the nesting already gives it.
