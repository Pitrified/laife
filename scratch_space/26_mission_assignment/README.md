# Dynamic mission assignment

Replace the hardcoded `"Build a house"` mission with LLM-driven mission generation based on the current world observation. On first think cycle (or when a mission completes), the player asks a "mission generator" chain to propose a goal given what it sees. This makes gameplay emergent instead of scripted.

---

## Plan

### New files

| File                                           | Purpose                                                                                                                                      |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/laife/llm/mission_generator.py`           | `MissionGenerator` dataclass + `MissionGeneratorConfig`, `MissionGeneratorInput`, `MissionGeneratorResult` - same pattern as `PlayerPlanner` |
| `src/laife/prompts/mission_generator/v1.jinja` | System prompt: given `{{ observation }}`, `{{ player_state }}`, `{{ inventory }}`, propose one concrete mission objective                    |
| `tests/llm/test_mission_generator.py`          | Unit tests for the generator class (config instantiation, prompt variable guard, `ainvoke` with mocked chain)                                |

### Modified files

#### `src/laife/entities/player.py`

1. **Imports**: add `MissionGenerator`, `MissionGeneratorConfig`.
2. **`__init__`**: instantiate `self.mission_generator`; initialise `self.mission` as `Mission(objective="", status=MissionStatus.PENDING)` so the player has no active goal until the first iteration of `play()`.
3. **`_start_new_mission(objective: str)`**: accept the new objective as an explicit argument (instead of reusing `self.mission.objective`). Reset history and create a fresh `ACTIVE` mission with the given objective. Keeps the method synchronous.
4. **`_generate_mission_objective() -> str`** (new async method): calls `mission_generator.ainvoke(observation, player_state, inventory)`, logs the result, and returns the `objective` string.
5. **`play()`**: at the top of the loop, if the mission is PENDING or terminal, `await _generate_mission_objective()` then call `_start_new_mission(new_obj)`.

#### `tests/entities/test_player_lifecycle.py`

- Add `MissionGeneratorConfig` and `MissionGenerator` to the `patch.multiple` call in `_make_player` so mock construction still works.
- Update the three `_start_new_mission` tests to pass an explicit `objective` string (e.g., `"Build a house"`) to match the updated signature.

### Sequence of changes

1. Create `MissionGeneratorInput`, `MissionGeneratorResult`, `MissionGeneratorConfig`, `MissionGenerator` in `mission_generator.py`.
2. Write `prompts/mission_generator/v1.jinja`.
3. Patch `player.py` (`__init__`, `_start_new_mission`, `_generate_mission_objective`, `play`).
4. Update `test_player_lifecycle.py`.
5. Write `tests/llm/test_mission_generator.py`.
6. Verify: `uv run pytest && uv run ruff check . && uv run pyright`.
