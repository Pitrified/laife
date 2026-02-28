# Typed world responses (`WRes` subclasses)

Replace the generic `response_data: dict` in `WRes` with typed pydantic subclasses (`WResBuild`, `WResCraft`, `WResObserve`, `WResMove`). This eliminates stringly-typed payloads, adds validation at the boundary, and makes the player-side response handling safer and self-documenting.

## Plan

### Goal

Remove the untyped `response_data: dict` bag from `WRes` and replace every use-site with a typed pydantic model whose fields are self-documenting and validated on construction.

### New class hierarchy (`src/laife/entities/world_channel.py`)

```python
class WRes(BaseModel):           # pydantic base - just status
    status: WResStatus

class WResBuild(WRes):           # build action result (success or judge/spatial rejection)
    feedback: str

class WResCraft(WRes):           # craft action result
    feedback: str

class WResObserve(WRes):         # observation result
    observation: WorldMapObservation

class WResMoveStep(WRes):        # per-step move validation from WorldRunner
    new_position: Position | None = None   # set on SUCCESS
    obstacle: str | None = None            # set on ERROR

class WResMove(WRes):            # aggregated move result returned by Player.move()
    message: str

class WResPlan(WRes):            # player-local planner result
    sub_missions: list[str]
    reason: str

class WResError(WRes):           # fallback for unknown requests / internal errors
    message: str
```

### Changes by file

#### `src/laife/entities/world_channel.py`

- Convert `WRes` from a plain class to a pydantic `BaseModel` (keeps `status: WResStatus`; drops `response_data`).
- Add the seven typed subclasses listed above.
- Forward-reference imports in `TYPE_CHECKING` block for `WorldMapObservation`.

#### `src/laife/entities/world_runner.py`

| Method                    | Old return                            | New return                                     |
| ------------------------- | ------------------------------------- | ---------------------------------------------- |
| `judge_and_build`         | `WRes(..., {"feedback": ...})`        | `WResBuild(status=..., feedback=...)`          |
| `add_building` (internal) | `WRes(ERROR, {"message": ...})`       | `WResBuild(status=ERROR, feedback=...)`        |
| `judge_craft`             | `WRes(..., {"feedback": ...})`        | `WResCraft(status=..., feedback=...)`          |
| `observe_at`              | `WRes(SUCCESS, {"observation": obs})` | `WResObserve(status=SUCCESS, observation=obs)` |
| `move_player`             | `WRes(SUCCESS/ERROR, {...})`          | `WResMoveStep(status=..., ...)`                |
| unknown request handler   | `WRes(ERROR, {"message": ...})`       | `WResError(status=ERROR, message=...)`         |

#### `src/laife/entities/player.py`

- `observe()`: `wrsp.response_data["observation"]` → `cast(WResObserve, wrsp).observation`
- `move()` per-step error: `wrsp.response_data.get("obstacle", "unknown")` → `cast(WResMoveStep, wrsp).obstacle or "unknown"`
- `move()` aggregate returns: `WRes(SUCCESS/ERROR, {"message": ...})` → `WResMove(status=..., message=...)`
- `plan()`: `WRes(SUCCESS, {"sub_missions": ..., "reason": ...})` → `WResPlan(status=SUCCESS, ...)`
- `action_error()`: `WRes(ERROR, {"message": ...})` → `WResError(status=ERROR, message=...)`

#### `tests/entities/test_move_delta.py`

- `wrsp.response_data["message"]` → `wrsp.message` (wrsp is `WResMove`)

#### `tests/entities/test_world_map_observation.py`

- `res.response_data["observation"]` → `res.observation` (res is `WResObserve`)

#### `tests/llm/test_player_planner.py`

- `"sub_missions" in wrsp.response_data` → `wrsp.sub_missions`
- `"reason" in wrsp.response_data` → `wrsp.reason`

### Verification

```bash
uv run pytest && uv run ruff check . && uv run pyright
```
