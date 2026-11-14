---
status: in progress
---

# Phase 4 - PixiJS, zoom and pan, the player detail

## Overview

The world view moves to PixiJS with `pixi-viewport` for zoom and pan, and the panel gets a detail view for one player.
Decided with the user on 2026-11-14, after an assessment of the move to PixiJS: do it now and cleanly, so third-party files are vendored and checked rather than loaded from a CDN or committed.
The detail view changes phase 3's cards: a click on a player shows that player alone, with the whole mission tree.
Context: [`00_start.md`](00_start.md), [`03_page_skeleton.md`](03_page_skeleton.md) (its findings carry the quit fix below).

## Goals

1. Third-party JavaScript comes from a manifest in git, fetched and hash-checked into `cache/vendor/` by `make vendor`, and served only after a check.
2. The world is drawn by PixiJS; wheel zoom, drag, pinch on a phone, and a button to fit the world again.
3. A click on a player, in the world or in the list, replaces the list with that player's detail; back returns to the list.
4. Moves are animated between snapshots.
5. The page closes its own event stream before it sends quit.

## Plan

### Vendoring

The abyss pattern (`abyss/src/abyss/ui/vendor.py`, `ui/vendor.toml`), trimmed to what laife uses: npm packages only, no plain files.

- `ui/vendor.toml`: each npm package with its exact version, the `integrity` hash the npm registry publishes for its tarball, and the files to extract.
  - `pixi.js` 8.22.0, `dist/pixi.min.mjs`, a single-file ES module with no imports (8.23.0 is three days old; abyss waits a few weeks before taking a release).
  - `pixi-viewport` 6.0.3, `dist/pixi_viewport.js`, which imports `"pixi.js"` by name. The 7.x line is under two weeks old; 6.0.3 has `pixi.js >= 8` as its peer.
- `laife.web.vendor`, run as `python -m laife.web.vendor` by `make vendor`: downloads each tarball over https that is not cached yet, refuses it unless its sha512 matches the pin, extracts only the listed files into `cache/vendor/<package>/`, and writes a lock with each file's sha256.
- `GET /vendor/<package>/<path>`: serves a listed file after checking it against the lock; a file not in the manifest is `404`, a file whose hash changed is refused with `500` and a message naming it, a missing cache says to run `make vendor`.
- `index.html` gets an import map: `"pixi.js"` to `/vendor/pixi.js/dist/pixi.min.mjs`, `"pixi-viewport"` to its file. The server allows nothing else; no CDN.
- `make e2e` depends on `make vendor`; `make check` does not need the network.
- How much of abyss's module is copied: Q17.

### World on PixiJS

`world.js` is rewritten; `players.js` and `api.js` keep their shape.

- An `Application` with `resizeTo` the pane, WebGL preferred. A `Viewport` holds three layers: terrains, buildings, players.
- Terrains and buildings are `Graphics` rectangles and `Text` names, in the colours of phase 3. They are rebuilt only when the snapshot's lists change.
- One `Sprite` per player, kept by name, with its texture switched by state from `/sprites`, centred on the position, the name under it, an outline when selected.
- Viewport: `drag()`, `pinch()`, `wheel()`, `decelerate()`, `clampZoom` between showing the whole world and about 4x. The world size is phase 3's grow-only bounds; the first snapshot fits the view to it, and a fit button at the top does it again.
- A click is the viewport's `clicked` event, which pixi-viewport does not fire after a drag; the player under it is found in world coordinates, as `playerAt` does now.
- Moves: when a snapshot moves a player, its sprite slides from where it is drawn to the new position over 200 ms on the ticker. A player more than a few hundred pixels away jumps instead.

### The panel: list and detail

- List mode: phase 3's cards, unchanged except that a card is shorter (latest three actions).
- Detail mode, when a player is selected: only that player.
  - Head: sprite, name, type, state, turn, position.
  - Mission tree, whole: each node with its objective, status, and failures as `consecutive_failures / max_failures`, nested by `steps`. The path to the active focus is highlighted, finished nodes are dimmed.
  - Inventory: name and description per utensil; "empty" when there is none.
  - Actions: the stream list for the player, longer than on the card (30 kept). What else goes here: Q18.
  - A back button, and Escape, return to the list.
- Selecting from the world or from the list does the same; selecting another player switches the detail. What the view does on select: Q19.

### Quit

`act("quit")` closes the `EventSource` before the request, so the page does not reconnect to the server it is stopping (phase 3 finding).

## Tests

- Unit, `make check`, no network: the manifest loads; a tarball with the wrong hash is refused; only listed files are extracted; a cached file edited after extraction is refused by the route; a path outside the manifest is `404`; the import map's targets are all in the manifest. Tarballs are built in the test, not downloaded.
- Browser, `make e2e`, after `make vendor`:
  - the canvas is drawn: an element screenshot has more than a few colours (Q20 for the tool);
  - wheel over the canvas zooms and the fit button restores it, read from a `data-zoom` attribute the page keeps on the canvas;
  - a click on a card shows the detail of that player alone, with at least one mission node after a step; back shows both cards again;
  - phase 3's step, pause and quit checks still pass, with no reconnect after quit.
- On g4, by the user: zoom, drag, a click on a player in the world, the detail view, pinch if tried on the phone.

## Out of scope

- A sprite atlas, a tiled map, sprites for buildings (backlog "Sprite loading", "Visual wishes").
- Memories and interactions in the detail: the game does not keep them yet (backlog "Interaction memory").
- The live game serving the page (phase 5).
- A JavaScript linter; the JavaScript is still small.

## Done when

- `make check` passes without network access; `make vendor` then `make e2e` pass on g7, and the screenshot shows the PixiJS world and a detail view.
- The user has checked zoom, pan, selection and the detail on g4.

## Open questions

- Q17: How much of abyss's vendoring to take.
  - a. A trimmed copy in `laife.web.vendor`: npm packages, integrity check, extraction of listed files, lock, checked serving; no plain-file pins. A backlog note that abyss and laife now hold the same code, for a shared package later.
  - b. A full copy of abyss's module, plain files included.
  - c. Extract a shared package from abyss first, used by both repos.
  - Recommended: a, because laife needs only npm packages, and a shared package is its own effort across two repos.
  - ANS: a.
- Q18: The detail's actions.
  - a. The stream list only, longer than on the card.
  - b. Also the snapshot's `history`, which has the action's fields and the full result text but only for the current mission step.
  - Recommended: a; the stream list covers more turns, and two lists of the same actions would confuse.
  - ANS: a.
- Q19: What the view does when a player is selected.
  - a. Centre on the player once, animated.
  - b. Follow the player while it is selected.
  - c. Nothing.
  - Recommended: a; following fights the user's own drag.
  - ANS: a.
- Q20: The tool for "the canvas is drawn". A WebGL canvas cannot be read with `getImageData`.
  - a. Pillow in the e2e group, counting colours in an element screenshot.
  - b. PixiJS's `extract`, called through a hook the page exposes for tests.
  - Recommended: a; it checks what reached the screen, and the page keeps no test hook.
  - ANS: a.

## What the implementation found

- `pixi.js` 8.22.0's `dist/pixi.min.mjs` has no imports, and `pixi-viewport` 6.0.3 imports only `"pixi.js"`; one import map entry each was enough. Both tarballs matched their pins on the first `make vendor`.
- The secrets hook read the integrity hashes in `ui/vendor.toml` as secrets; the manifest is excluded as `uv.lock` already was, and as abyss excludes its own.
- `create_app` passed ruff's complexity limit once the vendor route came in; its routes are now three groups (world, control, files), the file group mounted last.
- The detail first rendered without the card styles, which were scoped to `.player`; head, meta and action styles are now shared.
- The first quit check passed even without the fix: its listener was attached after the click, and Chromium waits about 3 s before an `EventSource` reconnects. It now records every request from before the click and waits 4 s; without the fix it catches the page's `/state` after the quit.
- A new player was first placed by testing for position (0, 0), wrong for a player standing at the origin; a flag replaced it.
- Seen on a long run: after 122 turns of the script p0 carries 20 hammers, and the mission tree shows its steps only while the mission is active, since a build or craft completes the root (backlog).
- Headless Chromium on g7 renders WebGL in software and logs "GPU stall due to ReadPixels" when a screenshot reads the canvas; a console warning, not a page error.
- `make e2e` now takes about 11 s, 4 of them the wait after quit.
