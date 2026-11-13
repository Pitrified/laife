---
status: in progress
priority: 1
description: |
  Which frontend shows the world and how it talks to the game loop: pygame as now, pygame-ce, a web app served from g7, or an engine such as Godot or Flutter.
  Decides the fate of folder 34's parked phases, the Python pin and the visual wishes in `plan.md`.
---

# Renderer choice - bootstrap

Picked from the `plan.md` backlog item "Renderer: pygame or a web app" on 2026-11-13.
The item came from the reboot, `36_reboot/00_start.md` D8.

## The user's framing, 2026-11-13

"frankly the webapp sounds quite neat"

Pro:

1. It can be run headless.
2. It has all the widgets we want from CSS and HTML. The target is a split screen: the world on the left, the players on the right with their latest actions; a click on a player shows its details: inventory, memories, interactions, mission (only the mission exists today).
3. Buttons for pause, play and step, and zoom with the mouse.
4. Cross platform.

Con:

1. A richer world with sprites is coming. How does that work with a canvas in HTML, or whatever does it? Blitting works well in pygame.
2. The game loop is a different paradigm. The world renderer sends events and the page picks them up, through a socket or SSE, and signals go back. Trickier.

The backlog item listed a third option, a text-only runner beside a renderer (`scratch_space/rebirth_/`); `make headless` is that runner now.
It also tied the terminal output, the log shape and the visual wishes to this choice; those stay in `plan.md` as their own items.

"Dependencies are never an issue": the number of new packages is not a cost in this assessment.

## Current state

Read 2026-11-13.

- `WorldRunner` imports no pygame; `make headless` runs the full engine without it.
  pygame is confined to `src/laife/rendering/` (renderer and sprites) and `game/main.py`.
- `WorldRenderer.render()` is one more coroutine in the `asyncio.gather` of `game/main.py`.
  It polls the runner's entity lists every 0.1 s, redraws at most once a second (`redraw_period_sec = 1`), and pumps pygame events: `q` quits, space toggles pause, `n` steps.
- The drawing is flat: terrain as coloured rectangles (`_TERRAIN_COLORS`), a sprite per player and per building.
- `SimControl`'s trigger methods are synchronous on purpose, so an event pump can call them. A request handler on the same event loop can call them the same way.
- The structured log (`slog`) already records every request, LLM call and step with player and turn; `make tui` reads it.
- What the players' side panel would show exists for some fields: `Player.render_state()`, `Mission.to_prompt()`, `Player.inventory`. Memories and interactions do not exist yet (backlog "Interaction memory").
- pygame 2.6 has no 3.14 wheel, so with the `==3.14.*` pin every machine builds it from source, which needs the SDL and freetype headers; g7 uses uv's managed Python for that reason. The pin is not the problem, the missing wheel is.
- g7 has node 22, and Playwright's Chromium and headless shell in `~/.cache/ms-playwright` (abyss uses them for `make e2e`).
- uvicorn, aiohttp and websockets are already in laife's lock, pulled by chromadb.

## Two decisions inside one

The question splits:

- **A. The seam.** How any view reads the world and sends commands back. Today it is in-process: the renderer reads Python objects.
  Every option other than pygame needs a protocol: a state snapshot, a stream of what changed, and a control channel.
- **B. The client.** What draws the world and the panels.

A is mostly independent of B. A protocol written for a browser serves a Godot or Flutter client unchanged, and also lets the TUI or a test read live state. So A can be built and checked headless first, and B can change later without touching the engine.

## The loop paradigm, user con 2

It is less different than it looks, because the current renderer already polls.

- **Snapshot:** `GET /state` returns the world as JSON: terrains, buildings, players with position, state, mission, last action. `Building`, `Terrain` and `Mission` are pydantic models, so they dump as they are; `Player` is a plain class and needs a snapshot model of its own.
  A page that fetches it once a second does what `WorldRenderer.redraw()` does now.
- **Events:** `GET /events` as Server-Sent Events: one message per world event (a move step, a build, a mission change, an LLM call). The browser `EventSource` reconnects by itself. The source is the same place `slog` writes, so the page and the log cannot disagree.
- **Control:** `POST /control/pause`, `/resume`, `/step` call `SimControl`. Commands are rare and small, so plain POSTs suffice.
- SSE plus POST covers both directions. WebSocket is the alternative when commands become frequent (dragging, live chat with a player); nothing planned needs it.
- The server runs as one more task in the same `asyncio.gather`, so it reads live objects with no locking: uvicorn's `Server.serve()` or aiohttp's `AppRunner` both run as a coroutine.
- The browser animates between states itself (`requestAnimationFrame`, interpolating a move), so smoothness does not depend on how often Python sends.

Replay comes nearly free: the same events read from a `cache/game_*.jsonl` instead of a live stream drive the same page.

## Sprites in a browser, user con 1

Canvas 2D `drawImage` from a sprite sheet is the browser's blit, and at laife's scale (a few players, tens of buildings, a tiled map) it is more than fast enough.
When the world grows, the usual step is a WebGL 2D renderer, which batches sprites on the GPU:

- **PixiJS:** a renderer only. Sprites, sprite sheets, tiling sprites, text; `pixi-viewport` adds drag, wheel zoom and pinch. Fits a view whose loop lives in Python.
- **Phaser:** a full game framework: loads tilemaps from the Tiled editor, cameras with zoom and follow, input, tweens. Its own game loop and physics would sit unused, since the world is authoritative in Python.
- **Kaplay, Excalibur:** smaller frameworks in the same space as Phaser.

The map can be authored in Tiled either way: its JSON export is read by Phaser directly and by PixiJS through a loader.
The side panel is HTML, not canvas, which is where the browser is strongest: lists, scrolling text, click handlers, CSS layout.

## Options

### pygame, as now

Pro:

- It works, and it is all Python.
- Blitting and sprite groups are native.
- One process, nothing served.

Con:

- Every widget is drawn by hand: the split screen, a scrolling action list, a clickable player card and its detail view are each custom code (`pygame_gui` helps, with its own look and limits).
- It needs a display. Agents on g7 see nothing; `SDL_VIDEODRIVER=dummy` plus saved frames is the only check without a screen.
- One viewer, on the machine running the game. No phone; g4 only through X forwarding, untested.
- pygame 2.6 has no 3.14 wheel, hence the source build and the pin question.
- Its calls are synchronous inside the asyncio loop; a slow frame stalls the world for that frame.
- Folder 34's two parked bugs stay: `SystemExit` on quit and the AVX2 notice.

### pygame-ce

The community fork, imported as `pygame`; for laife's use it is close to a drop-in.

Pro over pygame:

- More active releases, wheels for new Python versions sooner, and AVX2 builds (folder 34 phase 3 goes away). Whether a 3.14 wheel exists for g7 and g4 is to verify, not assumed.
- Additions: float rects, a window API, better text.

Con: everything in the pygame con list except the wheel and AVX2 points.

### Web app served from g7

The page runs in a browser; the Python game serves it on the tailnet. abyss's `ui/` is the precedent: a static server in Python, vendored JS pinned by version and hash in `ui/vendor.toml`, plain ES modules with no build step, Playwright tests in `make e2e`.

Pro, beyond the user's four:

- **An agent can see it.** Playwright in headless Chromium loads the page against `make headless`, clicks, and takes screenshots. This is the backlog item "Renderer checks without a screen" solved with the same tool abyss uses.
- **Any number of viewers:** g4, the phone, two tabs. A tab closed does not stop the game.
- **pygame leaves the dependencies,** so nothing builds from source and the 3.14 pin costs nothing.
- **Replay and live use one page** (see the loop section above).
- **The TUI's job can move into the page:** the per-player log, the LLM calls, prompts and replies, which the browser shows better than a terminal. Whether `make tui` stays is a later choice.
- **Folder 34 phase 1 stops existing:** the server is cancelled with the rest of the gather; no `sys.exit()` inside a task.

Con, beyond the user's two:

- **A second language.** The client is JavaScript (or TypeScript with a build step), with its own tests.
- **A protocol to keep in step:** the JSON shape of the snapshot and the events is a contract between Python and JS. Pydantic can emit a JSON Schema for it, which a test can check against what the page reads.
- **Something listens on the network.** Bind `127.0.0.1` by default, the tailnet address by choice; the control endpoints have no auth, which the tailnet makes acceptable for now.
- **Developing the page needs a world that keeps running.** `make headless` stops after `TURNS`; a paced or endless headless mode with the scripted LLM is needed so the page can be worked on without spending credit.
- **Rendering is now two processes apart from the state** in the replay case, and one network hop away in the live case: what the page shows can lag what the world did by up to one event.

### Python-only web frameworks

NiceGUI, Reflex, Panel, Streamlit: widgets written in Python, the browser handled by the framework.

- NiceGUI is the closest fit: FastAPI underneath, a WebSocket kept by the framework, the widgets the side panel needs, and it can run inside an existing asyncio loop.
  The world view would still be custom: an SVG or canvas element fed from Python, or a custom JS component. Sprites and zoom end up as JavaScript anyway, behind one more layer.
- Streamlit reruns the script on every interaction, which does not fit a long-running game loop.
- Reflex compiles to a React app with its own build and state model, heavy for a view.

Pro: no JavaScript for the panels. Con: the hard part, the world canvas, is JavaScript regardless, and the framework sits between it and the protocol.

### Other Python desktop libraries

- **Arcade** (on pyglet, OpenGL): sprites with GPU batching, cameras with zoom, tilemaps from Tiled, a GUI module. Clearly better than pygame for a richer world.
  It still needs a display and is still one viewer.
- **pyglet:** what Arcade is built on, lower level.
- **Pygbag:** compiles a pygame program to WebAssembly for the browser. It would move the Python game into the page, OpenAI key included; rejected.
- **Textual through `textual-serve`:** the existing TUI in a browser tab, no sprites.

### Game engines as the client

- **Godot:** an editor for tilemaps and scenes, a strong UI system, exports to desktop, web and Android; GDScript or C#. It would talk to the Python world over the protocol from seam A.
  Pro: the strongest path to a rich world. Con: a second runtime and editor, scene files in git, an export step, and an agent on g7 can run it headless but checking what it shows is harder than with a page.
- **Flutter with Flame:** Dart; Flame does sprites, tilemaps and cameras; Flutter's widgets are good for the side panel; builds for web, desktop, Android.
  Con: an SDK install on g7 (a system-level change), a build step, and a web build heavier than a page.
- **Unity:** C#, licence terms, heavy editor, no fit for agent work on g7. abyss rejected it as a starting point for the same reasons.
- **Bevy (Rust), LÖVE (Lua), raylib:** desktop-first, a new language, nothing a browser does not give here.
- **Tauri or Electron:** a desktop window around the web app; only if a native window is ever wanted, and then the web app is still the thing built.

## Assessment

- The user's wishes (split screen, clickable players, buttons, zoom, phone and g4) are what the browser is best at and what pygame is worst at.
- The worry about sprites does not hold at this scale: Canvas 2D covers it, and PixiJS or Phaser cover far more than laife will draw.
- The paradigm change is smaller than expected: the renderer already polls; snapshot, SSE and POST are the same shape over HTTP.
- The deciding argument for the agent workflow: a page can be run and looked at headless on g7, which no desktop option allows.
- Godot and Flutter stay as later clients over the same protocol if the world outgrows a page. Building seam A first keeps that door open.

Recommendation, before the questions below: build seam A, then a web client with plain Canvas 2D and HTML panels, PixiJS when sprites arrive; retire pygame when the page covers what the window does.

## Decisions 2026-11-14

Taken with the user, from Q1-Q9 below.

- The web app replaces pygame: a FastAPI server inside the game's asyncio loop, `GET /state`, SSE events and POST control; a page of plain ES modules with vendored libraries, Canvas 2D for the world and HTML for the panels.
- The protocol comes first, and it stays easy to change: one module of models, a contract test, no versioning.
- The Python pin stays at 3.14. The pin was never the problem; pygame's missing wheel was, and it leaves with pygame.
- `localhost` by default, the tailnet address by choice.
- The TUI stays; trimming it is part of the backlog item on terminal output and log shape.

## Phases

Each depends on the one before. The sub-plans are not written yet.

1. **World protocol, no client.** Snapshot, event stream and control endpoints served from the game's asyncio loop; a headless mode that keeps running; tests against the headless engine.
2. **Page skeleton.** Split screen: the world drawn from the snapshot on a canvas, players with their sprites, the player list with latest actions, pause, resume and step. Playwright check on g7 with a screenshot.
3. **Player detail and zoom.** A click opens the player card (state, mission tree, inventory, recent actions); wheel zoom and drag; events animate moves.
4. **Retire pygame.** `make run` serves the page instead of opening a window; pygame and `src/laife/rendering/` removed, the sprite loading moving to whatever serves the PNGs; folder 34 phases 1 and 3 discarded; the pygame build notes in `CONTRIBUTING.md` and the instructions removed. The 3.14 pin stays.

Sprites, a tiled map and replay from a log are their own folders after this one.

## Open questions

- Q1: Seam first? Phase 1 builds the protocol with no client, checked headless, before any page exists.
  - a. Yes, protocol first, then the page.
  - b. Page and protocol together, one phase.
  - Recommended: a, because the protocol is the part every client shares and it is fully checkable on g7 by an agent.
  - ANS: a, with a condition: the protocol must stay cheap to change. It is not a published API; the page and the server live in one repo and change in one commit. One module holds the models, and the contract test catches drift between them and the page, rather than a version scheme freezing it.
- Q2: The client for the world view.
  - a. Plain Canvas 2D and HTML panels now, PixiJS when sprites arrive.
  - b. PixiJS from the start.
  - c. Phaser from the start, for Tiled maps and cameras.
  - d. NiceGUI for the panels, a custom canvas for the world.
  - e. Godot or Flutter.
  - Recommended: a, because a few rectangles do not need WebGL, and the move to PixiJS only touches the world canvas. b is close behind if zoom and pan from `pixi-viewport` are wanted in phase 3 rather than written by hand.
  - ANS: a, plain Canvas 2D for now. Player sprites already exist: per-state PNGs under `static/sprites/inu/`, chosen by `SpriteLoader` in `src/laife/rendering/sprites.py`. The page draws them with `drawImage`, so phase 2 shows sprites for players and rectangles for the rest.
- Q3: Transport.
  - a. `GET /state` snapshot, SSE for events, POST for control.
  - b. One WebSocket for everything.
  - c. Polling `GET /state` only, no events.
  - Recommended: a, because it covers both directions with browser built-ins and each piece is testable with plain HTTP; c is the fallback for phase 2 if events slip.
  - ANS: a.
- Q4: The server library, running as a task in the game's `asyncio.gather`.
  - a. Starlette with uvicorn (uvicorn already in the lock).
  - b. FastAPI on the same, for the pydantic request and response models.
  - c. aiohttp (already in the lock).
  - d. stdlib `http.server` as abyss does; it is threaded, so reads of live game state would cross threads.
  - Recommended: b, because the snapshot and events will be pydantic models, and FastAPI emits their schema for the contract test.
  - ANS: b, FastAPI on uvicorn.
- Q5: JavaScript tooling.
  - a. Plain ES modules, no build, vendored libraries pinned in a manifest, as abyss's `ui/vendor.toml`.
  - b. TypeScript with a bundler (Vite), `node_modules` on g7.
  - Recommended: a, because abyss already runs it with Playwright on g7 and the page is small; b when the client grows types worth checking.
  - ANS: a.
- Q6: pygame after the page exists.
  - a. Retired in phase 4, once the page covers the window.
  - b. Kept beside the page as a local window.
  - c. Swapped for pygame-ce and kept.
  - Recommended: a, because two renderers double every visual change, and keeping pygame keeps the pin and folder 34's bugs.
  - ANS: a, retired.
- Q7: Where the page is reachable.
  - a. `127.0.0.1` by default, the tailnet address with a flag; no auth.
  - b. The tailnet address always.
  - Recommended: a, the abyss default; g4 reaches it with an SSH tunnel or the flag.
  - ANS: a.
- Q8: A headless mode that keeps running, for developing the page without spending credit.
  - a. `make headless` gains a paced, endless option (`TURNS=0`, a delay per turn).
  - b. A separate target, `make serve-headless`, scripted LLM plus the server.
  - Recommended: b, because the existing `make headless` stays the quick gate and the serving variant is its own thing.
  - ANS: a or b, whichever is neater; the user leaves the shape to the plan. Decided in phase 1's plan.
- Q9: Does the TUI stay?
  - a. Stays as is; the page is the main view.
  - b. Its views move into the page over time, then it goes.
  - Recommended: a for this folder; the page needs to exist before replacing anything.
  - ANS: a. Trimming the TUI belongs to the backlog item "Terminal output and log shape".
