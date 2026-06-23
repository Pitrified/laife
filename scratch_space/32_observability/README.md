---
status: draft
---

# Observability

## draft

missions, interactions, world state, actions are too opaque

terminal output is too fast

struct log is too obscure

we need some sort of observability

how flexible is pygame? rendering custom "widget" spirals into a nightmare?

> Pygame is flexible at the pixel level but gives you nothing above it: no
> layout, no event/focus model, no widget tree. You get a surface, blitting,
> font rendering, and an event queue, and everything else is yours to build.
> So a single custom widget (a panel that draws text/bars from world state) is
> easy: clear a rect, blit some text, done. The nightmare is the *second* and
> *third* widget, when you start wanting scrolling, hit-testing, resizing,
> z-order, and dirty-rect redraws - you end up reimplementing a GUI toolkit by
> hand.
>
> Options, cheapest first:
> - Stay in pygame and keep widgets dumb: fixed rects, full redraw each frame,
>   no interaction. Fine for a read-only observability overlay.
> - Use `pygame_gui` for real widgets (buttons, panels, scrolling text,
>   themable via JSON) without writing the toolkit yourself.
> - Decouple entirely: emit struct log / state to a separate process and render
>   it with a tool built for inspection (a small web UI, Textual TUI, or
>   matplotlib), leaving pygame to the simulation only.
>
> For "missions/interactions/world state are too opaque", the decoupled route
> is usually the better long-term answer: the observability surface evolves
> independently of the game loop and can pause, scroll back, and filter.

we decouple completely

1. analyze what we are emitting in the struct log and which metadata we have to filter on

   The JSON-lines sink is already in place: `configure_logging()` in
   `src/laife/meta/logger.py` writes one serialized loguru record per line to
   `cache/game_<timestamp>.jsonl`, and `slog` is the bound logger every call
   site must use. So the raw material exists; this step is cataloguing it.

   - Inventory the event types. They are constants in
     `src/laife/meta/log_events.py`: `action`, `world_response`,
     `mission_transition`, `llm_call`, `llm_result`, `world_request`. Every
     structured record carries `event=<one of these>` plus loguru's own
     `time`, `level`, `message`. `world_request` is emitted at `DEBUG`; the
     rest at `INFO` - so the file `level` determines whether requests even
     appear.
   - Map the per-event payload (the fields passed to `slog.bind(...)`), since
     these are exactly what the UI filters and groups on:
     - `action`: `player`, `action`
     - `world_response`: `player`, `kind` (build/craft/...), `status`
     - `mission_transition`: `player`, `to_status`
     - `llm_call`: `model`, `elapsed`
     - `world_request`: `kind` (request class name)
   - Identify the natural filter axes from the above: **player** (present on
     most player-side events, absent on `world_request`/`llm_call`),
     **event type**, **status** (success/failure on responses and missions),
     and **time**. Note the gaps to close before the UI is useful: there is no
     correlation id tying an `llm_call` -> resulting `action` -> `world_request`
     -> `world_response` together, and no tick/turn number. Decide whether to
     add a `player`/`turn`/`request_id` field at the bind sites so the
     observability view can reconstruct a single interaction end to end.
   - Confirm there is no PII/secret leakage in serialized records (e.g. LLM
     prompts or keys) before anything renders them.

1. propose various ui options (pygame overlay, pygame_gui, textual, web, ...) and their tradeoffs

   Tail the `.jsonl` file (or a queue/socket fed by the same records) and
   render it. Options, cheapest first:

   - **pygame overlay (dumb widgets)** - draw a read-only panel in the
     existing pygame surface, full redraw each frame, fixed rects. Cheapest to
     wire up and stays in-process, but you build scrolling/filtering/hit-test
     by hand and it competes with the game for the same event loop and frame
     budget. Fine only for a tiny always-on HUD.
   - **`pygame_gui`** - real widgets (scrolling text box, buttons, themable
     panels) without writing the toolkit. Still in-process and still coupled to
     the game loop, but interaction is feasible. Adds a dependency and a theme
     file; good if you want the inspector *inside* the game window.
   - **Textual (TUI)** - a separate process tailing the file in the terminal.
     Gets you tables, filtering, scrollback, and key bindings nearly for free,
     decoupled from the game loop, no graphics stack. Best effort-to-payoff for
     a developer-facing tool; weak for anything spatial/visual.
   - **Web (FastAPI + small frontend / or a notebook)** - the file or a
     websocket feeds a browser UI. Most flexible for rich filtering, timelines,
     and later sharing; can pause, scroll back, and replay independently of the
     sim. Highest setup cost and a second runtime to manage.

   Recommendation: since we already decided to decouple completely, start with
   **Textual** for the day-to-day debugging view (fast, terminal-native,
   reads the existing `.jsonl`) and keep the **web** option open for when we
   want timelines/replay. Keep pygame out of the observability path.

1. add a way to stop the game loop (an event in pygame i guess)

   To inspect state we need the simulation to hold still. Because the loop is
   asyncio-driven (see `world_runner.py` awaiting on `input_queue`) and not a
   classic pygame blit loop, "pause" means pausing the async stepping, not just
   freezing the screen.

   - Define a shared pause flag/`asyncio.Event` that the world runner and
     player tasks check before advancing a step (e.g. `await
     pause_event.wait()` gating the top of the run loop). Set/clear it to
     pause/resume; in-flight LLM calls finish, then everything blocks before
     the next action.
   - Wire a trigger. If a pygame window is in focus, watch for a `KEYDOWN`
     event (e.g. space) in the event pump and toggle the flag. If the inspector
     is the decoupled Textual/web UI, expose pause/resume/step there and have
     it set the same flag (via a small control queue or, for the web case, an
     endpoint) so you can drive the sim from the observability tool itself.
   - Add a **single-step** control alongside pause: clear the event, let
     exactly one step run, re-set it. This is what makes the log readable -
     advance one interaction, read it, advance again.
   - Emit a `mission_transition`-style marker (or a new `paused`/`resumed`
     event) so the pause itself shows up on the timeline.
