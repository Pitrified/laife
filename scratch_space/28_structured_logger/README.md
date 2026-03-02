# Structured game logger

Add a `structlog`-based file sink that records every action, world response,
mission transition, and LLM call as JSON lines. `Alog` is kept untouched for
real-time console feedback during development. The two loggers run in parallel:
`alg.log()` prints to the terminal as before; `slog.info()` writes structured
records to a rotating JSON-lines file.

---

## Why dual loggers?

`Alog` provides immediate, human-readable terminal output that is essential
during active development - duplicate suppression, in-place `(xN)` counters,
and zero configuration. Replacing it would lose that feedback loop.

`structlog` handles the orthogonal concern of machine-readable persistence:
timestamped JSON lines that survive a session, can be diffed between runs, and
feed an analytics dashboard later. Keeping them separate means neither system
compromises the other.

Add the dependency:

```
uv add structlog
```

---

## Plan

### New files

| File | Purpose |
| ---- | ------- |
| `src/laife/meta/logger.py` | `configure_logging(level, log_file)` factory + `get_logger(name)` wrapper; configures structlog with a **file-only** JSON sink (no console renderer) |
| `src/laife/meta/log_events.py` | String constants for all structured event names |
| `tests/meta/test_logger.py` | Unit tests confirming JSON output, level filtering, and file writing |

### Modified files

#### `src/laife/meta/logger.py`

- `configure_logging(level: str = "INFO", log_file: str | Path = "cache/game.jsonl") -> None`:
  - Configures structlog processor chain:
    1. `structlog.contextvars.merge_contextvars` - injects per-task context
       bound via `structlog.contextvars.bind_contextvars` (e.g. player name).
    2. `structlog.processors.add_log_level`
    3. `structlog.processors.TimeStamper(fmt="iso")`
    4. `structlog.processors.JSONRenderer()` - always JSON; no console renderer.
  - Routes output through a stdlib `logging.FileHandler` pointed at `log_file`.
    The file is opened in append mode so successive runs accumulate.
  - The log file name includes a UTC timestamp suffix so runs do not overwrite
    each other: `cache/game_2026-03-01T120000.jsonl`.
  - Called once at startup from `game/main.py` **before** the asyncio loop.
- `get_logger(name: str) -> structlog.BoundLogger`: thin wrapper so call sites
  never import `structlog` directly.
- Module-level instance: `slog = get_logger("laife")`.

#### `src/laife/meta/log_events.py`

```python
EVT_ACTION             = "action"
EVT_WORLD_RESPONSE     = "world_response"
EVT_MISSION_TRANSITION = "mission_transition"
EVT_LLM_CALL           = "llm_call"
EVT_LLM_RESULT         = "llm_result"
EVT_WORLD_REQUEST      = "world_request"
```

#### `src/laife/entities/player.py`

`alg.log(...)` calls are **not removed**. Structured calls are added alongside
them at the four high-value sites:

- After picking an action:
  ```python
  alg.log(f"PLAYER.play {self.name}: picked {action}")
  slog.info(EVT_ACTION, player=self.name, action=action.model_dump())
  ```
- After a build/craft response:
  ```python
  alg.log(f"PLAYER.build {self.name}: got response {wrsp}")
  slog.info(EVT_WORLD_RESPONSE, player=self.name, kind="build", status=wrsp.status.value)
  ```
- On mission status transition (inside `_update_mission_from_response`):
  ```python
  slog.info(EVT_MISSION_TRANSITION, player=self.name, to_status=self.mission.status.value)
  ```
- Bind player context once per `play()` loop iteration:
  ```python
  structlog.contextvars.bind_contextvars(player=self.name)
  ```

#### `src/laife/entities/world_runner.py`

`alg.log(...)` calls are **not removed**. Add one structured call per request
handled:

```python
slog.debug(EVT_WORLD_REQUEST, kind=type(player_input).__name__)
```

#### `src/laife/llm/player_brain.py`

Wrap each `chain.ainvoke(...)` call with timing. `Alog` has no hook here today,
so this is a net-new log site:

```python
t0 = time.monotonic()
result = await chain.ainvoke(...)
slog.info(EVT_LLM_CALL, model=self.config.model, elapsed=round(time.monotonic() - t0, 3))
```

#### `game/main.py`

Call `configure_logging()` before the asyncio event loop starts:

```python
from laife.meta.logger import configure_logging
configure_logging(level="INFO", log_file=f"cache/game_{timestamp}.jsonl")
```

#### `src/laife/ui/alog.py`

No changes. `Alog` remains the canonical real-time feedback channel.

### Log record shape (example)

```json
{"event": "action", "player": "Alice", "action": {"type": "ActionBuild", "building_type": "house"}, "level": "info", "timestamp": "2026-03-01T12:00:00.123Z"}
{"event": "llm_call", "model": "gpt-4o", "elapsed": 1.234, "level": "info", "timestamp": "2026-03-01T12:00:01.357Z"}
{"event": "mission_transition", "player": "Alice", "to_status": "completed", "level": "info", "timestamp": "2026-03-01T12:00:01.360Z"}
{"event": "world_request", "kind": "WRecBuild", "level": "debug", "timestamp": "2026-03-01T12:00:01.361Z"}
```

### Sequence of changes

1. `uv add structlog`.
2. Create `log_events.py` constants.
3. Create `logger.py` with `configure_logging` and `get_logger`; export `slog`.
4. Write `tests/meta/test_logger.py`:
   - JSON output shape matches expected keys.
   - Level filtering suppresses debug records at INFO level.
   - File sink writes to a temp path.
5. Add `slog` calls to `player.py` (alongside existing `alg.log`).
6. Add `slog` call to `world_runner.py`.
7. Add LLM timing in `player_brain.py`.
8. Update `game/main.py` startup call.
9. Verify: `uv run pytest && uv run ruff check . && uv run pyright`.
