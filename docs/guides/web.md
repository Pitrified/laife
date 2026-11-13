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

It listens on `127.0.0.1:8002` unless told otherwise, and stops on Ctrl-C.
The scripted model answers instantly, so a serving run waits `PACE` seconds before each answer; without that an endless run fills the log in seconds.
The players finishing their turns does not stop the server: the final state stays readable.

## Routes

| Route | Answer |
| --- | --- |
| `GET /state` | the world now: terrains, buildings, players with position, state, turn, mission tree, inventory and latest history |
| `GET /events` | Server-Sent Events, one per structured log record |
| `POST /control/pause`, `/control/resume`, `/control/step` | `{"paused": bool}`; `409` when the run has no pause control |
| `GET /openapi.json` | the schema of every route and model, from FastAPI |

```bash
curl -s http://127.0.0.1:8002/state
curl -sN http://127.0.0.1:8002/events
curl -s -X POST http://127.0.0.1:8002/control/step
```

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
