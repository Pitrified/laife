# Mission Step Runner

## Problem

The `play()` loop always passes `self.mission` (the top-level `Mission` object) to `think()`.
`Mission.status` is set once at creation and never updated. After `plan()` appends sub-missions,
the brain still sees the same broad objective and can re-plan indefinitely without making forward
progress. There is no mechanism to:

- focus the brain on one concrete sub-mission at a time,
- detect that a sub-mission is finished,
- advance automatically to the next pending step,
- propagate completion upward when all steps are done.

---

## Goal

Add a thin "focus cursor" to the mission tree and an `ActionComplete` signal so the brain can
close individual steps. Wire it into `play()` so the agent moves through the step list end-to-end.

---

## Patterns followed

| Reference                            | What to borrow                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------------- |
| `src/laife/entities/action.py`       | Add `ActionComplete` beside the existing action variants                        |
| `src/laife/llm/mission.py`           | New `Mission.active_focus()`, `Mission.advance()`, extend `to_prompt()`         |
| `src/laife/entities/player.py`       | `Player.complete()` handler mirrors `Player.plan()` structure                   |
| `src/laife/llm/player_brain.py`      | `PlayerBrain.think()` signature unchanged; caller changes the mission it passes |
| `src/laife/entities/world_runner.py` | No changes needed - completion is player-local                                  |

---

## New action: `ActionComplete`

Add to `src/laife/entities/action.py` alongside the existing variants:

```python
class ActionComplete(BaseAction):
    """Signal that the current focus mission has been achieved."""

    outcome: str = Field(..., description="One-sentence description of what was accomplished.")
```

Update the `Actions` union and the `match` block in `Player.play()`.

---

## Mission tree changes - `src/laife/llm/mission.py`

### `Mission.active_focus() -> Mission`

Walk the tree depth-first and return the first sub-mission whose status is `ACTIVE`.
If no sub-mission is `ACTIVE`, return `self`.

```python
def active_focus(self) -> Mission:
    """Return the deepest active sub-mission, or self if none."""
    for step in self.steps:
        if step.status == MissionStatus.ACTIVE:
            candidate = step.active_focus()
            return candidate
    return self
```

### `Mission.advance() -> bool`

After a step is marked `COMPLETED`, activate the next `PENDING` step.
Returns `True` if a new step was activated, `False` if none remain (all done or parent complete).

```python
def advance(self) -> bool:
    """Activate the next pending step. Return True if one was found."""
    for step in self.steps:
        if step.status == MissionStatus.PENDING:
            step.status = MissionStatus.ACTIVE
            return True
    # All steps completed - mark self completed and ask parent to advance
    self.status = MissionStatus.COMPLETED
    if self.parent_mission is not None:
        self.parent_mission.advance()
    return False
```

### `Mission.to_prompt()` - add focus marker

Prefix the focused step with `[FOCUS]` so the LLM knows exactly what to work on:

```
[M0] Build a house (active)
  [FOCUS][M1] Gather 5 logs (active)
  [M1] Craft a workbench (pending)
  [M1] Place foundation (pending)
[PM0]: Survive the first night (active)
```

---

## `Player.plan()` - activate the first sub-mission

After appending sub-missions, call `advance()` to activate the first one immediately:

```python
for sub_objective in result.sub_missions:
    self.mission.add_sub_mission(sub_objective)
self.mission.advance()          # activate step 0
self.history = MissionHistory()
```

Also update `add_sub_mission()` in `Mission` to leave new steps as `PENDING` by default
(already the case - no code change needed).

---

## `Player.play()` - focus the brain

Replace:

```python
action = await self.think()
```

with:

```python
action = await self.think(focus=self.mission.active_focus())
```

Update `think()` signature:

```python
async def think(self, focus: Mission | None = None) -> BaseAction:
    target = focus if focus is not None else self.mission
    return await self.brain.think(
        mission=target,
        history=self.history,
        observation=self.last_observation,
        player_state=self.render_state(),
    )
```

`PlayerBrain.think()` and `ActionPicker` are unchanged.

---

## `Player.complete()` handler

```python
async def complete(self, action: ActionComplete) -> WRes:
    """Mark the active focus mission done and advance to the next step."""
    focus = self.mission.active_focus()
    alg.log(f"PLAYER.complete {self.name}: completing '{focus.objective}'")
    focus.status = MissionStatus.COMPLETED
    advanced = self.mission.advance()
    self.history = MissionHistory()   # fresh slate for the new focus
    msg = (
        f"Completed '{focus.objective}'. "
        + (f"Next step: '{self.mission.active_focus().objective}'." if advanced else "All steps done.")
    )
    alg.log(f"PLAYER.complete {self.name}: {msg}")
    return WRes(WResStatus.SUCCESS, {"message": msg, "outcome": action.outcome})
```

Wire into `play()`:

```python
case ActionComplete() as act:
    wrsp = await self.complete(act)
```

---

## Data models summary

| Class / method         | File                 | Change                                 |
| ---------------------- | -------------------- | -------------------------------------- |
| `ActionComplete`       | `entities/action.py` | new                                    |
| `Actions` union        | `entities/action.py` | add variant                            |
| `Mission.active_focus` | `llm/mission.py`     | new method                             |
| `Mission.advance`      | `llm/mission.py`     | new method                             |
| `Mission.to_prompt`    | `llm/mission.py`     | add focus marker                       |
| `Player.think`         | `entities/player.py` | `focus` kwarg                          |
| `Player.plan`          | `entities/player.py` | call `advance()`                       |
| `Player.complete`      | `entities/player.py` | new handler                            |
| `Player.play`          | `entities/player.py` | pass focus; wire `ActionComplete` case |

No prompt changes. No `WorldRunner` changes.

---

## Tests - `tests/entities/test_mission_step_runner.py`

| Test                                       | What it checks                                                    |
| ------------------------------------------ | ----------------------------------------------------------------- |
| `test_active_focus_no_steps`               | `active_focus()` returns self when no sub-missions                |
| `test_active_focus_first_active_step`      | returns the first `ACTIVE` sub-mission                            |
| `test_active_focus_nested`                 | descends into nested sub-missions                                 |
| `test_advance_activates_next_pending`      | `advance()` flips the first `PENDING` step to `ACTIVE`            |
| `test_advance_returns_false_when_all_done` | returns `False` and marks parent `COMPLETED` when no steps remain |
| `test_plan_activates_first_sub_mission`    | after `Player.plan()`, first sub-mission is `ACTIVE`              |
| `test_complete_advances_to_next_step`      | `Player.complete()` marks focus done and activates next step      |
| `test_complete_resets_history`             | history is empty after `Player.complete()`                        |
| `test_complete_returns_success`            | `Player.complete()` returns `WRes(SUCCESS)`                       |
| `test_to_prompt_marks_focus`               | `[FOCUS]` appears on the active step in `to_prompt()`             |

Mirror test structure of `tests/llm/test_player_planner.py` - mock `ainvoke`, no real LLM calls.

---

## Implementation order

1. `ActionComplete` in `src/laife/entities/action.py`.
2. `Mission.active_focus()`, `Mission.advance()`, `Mission.to_prompt()` update in `src/laife/llm/mission.py`.
3. `Player.complete()`, `Player.think(focus=...)`, `Player.plan()` tweak, `play()` wiring in `src/laife/entities/player.py`.
4. `tests/entities/test_mission_step_runner.py`.
5. Verify: `uv run pytest && uv run ruff check . && uv run pyright`.
