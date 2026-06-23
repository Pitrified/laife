# Observability - bootstrap

## The idea

Missions, interactions, world state, and actions are too opaque. Terminal
output (`Alog` / `alg`) scrolls too fast to read, and the structured log is too
obscure to follow by eye. We need a real observability surface to watch and
debug the simulation.

Original draft and the analysis of each step live in [`README.md`](README.md).

## Current state

- A JSON-lines structured sink already exists: `configure_logging()` in
  `src/laife/meta/logger.py` writes one serialized loguru record per line to
  `cache/game_<timestamp>.jsonl`. `slog` is the bound logger; all structured
  calls flow through it.
- `Alog` (`src/laife/ui/alog.py`) remains the real-time console feedback
  channel and is unchanged by this work.
- Event names are constants in `src/laife/meta/log_events.py`: `action`,
  `world_response`, `mission_transition`, `llm_call`, `llm_result`,
  `world_request`.
- The game loop is asyncio-driven; `world_runner.py` awaits on `input_queue`.
  It is not a classic pygame blit loop, so "pause" means pausing async stepping.

## Decision: decouple completely

We considered three rendering routes (pure pygame overlay, `pygame_gui`, and a
fully decoupled inspector). We decouple completely: the observability surface
reads the existing `.jsonl` (or a queue/socket fed by the same records) in a
separate process, so it evolves independently of the game loop and can pause,
scroll back, and filter. Pygame stays out of the observability path.

Why not in-pygame: a single read-only widget is easy, but the second and third
widget (scrolling, hit-testing, filtering) means reimplementing a GUI toolkit,
and it competes with the game for the same event loop and frame budget.

## The three phases

1. Analyze what the struct log emits and which metadata we filter on.
2. Propose UI options and their tradeoffs; pick one to build.
3. Add a way to pause/step the game loop so state can be inspected.

## Open questions

- Do we add a correlation id (and turn/tick number) at the `slog.bind` sites so
  a single interaction (`llm_call` -> `action` -> `world_request` ->
  `world_response`) can be reconstructed end to end? Currently there is none.
- Is there any PII/secret risk in serialized records (LLM prompts, keys) before
  a UI renders them?
- Should pause/step be driven from a pygame `KEYDOWN`, or from the decoupled
  inspector itself (control queue / endpoint)?
