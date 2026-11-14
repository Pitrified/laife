---
status: in progress
---

# Phase 3 - Page skeleton

## Overview

The first page over the protocol of phases 1 and 2: the world on the left, the players on the right, and the run's controls.
It replaces nothing yet; `make run` keeps its pygame window until phase 5.
Context: [`00_start.md`](00_start.md) (the user's split-screen wish, Q2 plain Canvas 2D, Q5 plain ES modules), [`01_world_protocol.md`](01_world_protocol.md), [`02_clean_stop.md`](02_clean_stop.md).

## Goals

1. `make headless SERVE=1` serves a page at `/` showing the world and the players, live.
2. Pause, resume, step and quit from the page.
3. A browser test on g7 drives the page against a headless run and saves a screenshot.

## What the page shows

### World, left

- A `<canvas>` with the world in world coordinates, scaled to fit the pane. The world is in pixels already: pygame drew it 1:1 in a 1200 x 900 window.
- Terrains as filled rectangles in the colours `WorldRenderer` uses today, from `position` (top left) and `size`.
- Buildings as rectangles with their name, from `position` (top left) and `building_type.size`.
- Players as their sprite for the current state (`idle`, `thinking`, `moving`), centred on `position`, as `PlayerSprite` does, with the name under it. The selected player is outlined.
- What area the view covers: Q14.

### Players, right

- One card per player: sprite, name, state, turn, the mission objective and status, the active step when the mission has steps.
- Under it the player's latest actions, newest first: built from `action` and `world_response` events in the stream, not from the snapshot's `history`, which resets on a new mission, a plan and a completed step (phase 1 finding). The page keeps the last few per player; a page opened mid-run starts with none.
- A click on a card or on the player in the world selects it. Phase 4 opens the detail card from that selection; here it only highlights.

### Controls, top

- Pause or resume (one button showing the current state, from the snapshot's `paused`), step (enabled while paused), quit (asks for confirmation first).
- A status line: connected, reconnecting, or stopped. After quit, or when the server is gone, the page says the run has ended and stops retrying.

## How the page keeps up

- On load: `GET /state`, draw, then open `EventSource('/events')`.
- On each event: add it to the action list if it is an action or a world response, and schedule a `GET /state`, at most one every 250 ms. The snapshot is the truth for what is drawn; the events say when to fetch it and feed the action list.
  Ceiling: one snapshot fetch per 250 ms however busy the run is. That is fine at this size; phase 4 can apply move events to the drawing directly when moves are animated.
- Events with `seq` at or below the last snapshot's are still added to the action list (they are not drawn twice, since drawing comes from the snapshot alone).
- On a stream error the browser reconnects by itself; on reconnect the page refetches `/state`. Events published while disconnected are lost to the action list, which is acceptable for a view.

## Serving

- The page lives in `ui/world_web/` at the repo root: `index.html`, `style.css`, `js/` with one module per concern (`api.js` for the fetches, stream and controls, `world.js` for the canvas, `players.js` for the panel, `app.js` wiring them). This follows abyss's `ui/<name>/` layout, leaving room for other UIs.
- FastAPI mounts it with `StaticFiles` at `/`, and `static/sprites/` at `/sprites/`.
- No third-party JavaScript in this phase, so no vendor manifest yet; it arrives with the first library (PixiJS, or whatever phase 4 needs).
- The sprite file for each player type and state comes from the server, `GET /sprites`, so the page and the Python side read one table.
  That table, `STATE_FNS` in `src/laife/rendering/sprites.py`, moves to a module without pygame, since `laife.web` must not import pygame; the pygame loader imports it from there until phase 5 removes the loader.
- Responses for the page's files are `Cache-Control: no-cache`, so a reload after an edit picks the edit up.

## Tests

- Unit, in `make check`: `/` serves the page, `/sprites` lists a file for every `PlayerState` of every player type in use and each file exists, `/sprites/<file>` serves it.
- Browser, with Playwright and Chromium on g7: start `game/headless.py --serve --paused` as a subprocess on a free port (as `tests/web/test_stop.py` does), open the page, and check:
  - the canvas is not blank, and both player cards show turn 0;
  - step: one player's turn becomes 1 and its card gains an action;
  - resume then pause: turns advance, then hold;
  - quit: the status line says the run ended, and the process exits.
  A screenshot is written to `cache/e2e/` at the end, for an agent or the user to look at. Where these tests run: Q15.
- No JavaScript unit tests or linter in this phase; the browser test is the check. Q16 covers the tool.

## Out of scope

- The player detail card, zoom and pan, animated moves (phase 4).
- The live game serving the page (phase 5).
- Sprites for buildings and terrain, a tiled map, the sprite-atlas format (backlog "Sprite loading").
- Mobile layout beyond the panel stacking under the world on a narrow screen.

## Done when

- `make check` passes; the browser tests pass where Q15 puts them.
- On g7: the browser test's screenshot shows the world and both players.
- On g4, by the user: `make headless SERVE=1 TURNS=0` on g7, an SSH tunnel (`ssh -L 8002:127.0.0.1:8002 g7`), and `http://localhost:8002` in a browser shows the run moving; pause, step, resume and quit work.

## Open questions

- Q14: What area the world view covers. The game has no world size: pygame used its 1200 x 900 window, terrains reach about 900 x 800, players start within 800 x 600 and can walk anywhere.
  - a. Fit the view to the bounding box of everything in the snapshot, with a margin, and only ever grow it during a session, so the view does not jump on every move.
  - b. A world size constant (1200 x 900, from pygame) moved to `laife.config` and sent in the snapshot; a player outside it is clipped until zoom and pan exist.
  - Recommended: a, because it needs no constant the world logic does not have, and it keeps a wandering player in view.
  - ANS: a.
- Q15: Where the browser tests run.
  - a. A separate `make e2e`, marked `e2e` and left out of `make check`, as abyss does; every phase touching the page runs it before its commit.
  - b. Inside `make check`.
  - Recommended: a, because it starts Chromium and a subprocess game, a few seconds that grow with every page test, and needs the Playwright browsers, which a fresh clone does not have.
  - ANS: a.
- Q16: Tooling. `playwright` becomes a dev dependency, pinned `>=1.63,<1.64` as in abyss, which matches the Chromium (revision 1243) already on g7.
  No JavaScript linter in this phase.
  - a. Approved; the phase may run unattended once planned.
  - b. Approved, but add a JS linter (Biome or ESLint) now.
  - Recommended: a; a linter is worth adding when the JavaScript grows, phase 4 at the earliest.
  - ANS: a, approved; the phase may run unattended.
