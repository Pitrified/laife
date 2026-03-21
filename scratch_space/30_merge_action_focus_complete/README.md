# Merge main into feat/action_focus

## Overview

we are mid merge from `main` into `feat/action_focus`

there are some conflicts that need to be resolved
then we want to check that `feat/action_focus` still works as expected

1. analyze broken conflict files
2. search for scratch space files that helped implement the features
3. check the git history to understand the changes made in `main` that are causing the conflicts if needed
4. plan the conflict resolution

## Plan: Resolve feat/action_focus merge conflicts

Merge all non-overlapping additions from `main` (ActionInteract, mission lifecycle tracking, typed return types) into `feat/action_focus` (ActionComplete, focus-based mission stepping), resolving six conflict blocks across five files.

---

### Step 1 - action.py: include both new action types

In action.py: resolve the conflict by keeping `ActionComplete` (HEAD) and appending `ActionInteract` (main), then combining both into the `Actions` union:

```python
class ActionComplete(BaseAction):
    """Signal that the current focus mission has been achieved."""
    outcome: str = Field(..., description="One-sentence description of what was accomplished.")

class ActionInteract(BaseAction):
    """Send a natural-language message to a nearby player."""
    target_name: str = Field(..., description="Name of the player to address.")
    message: str = Field(..., description="The message to send.")

Actions = ActionMove | ActionBuild | ActionCraft | ActionPlan | ActionComplete | ActionInteract
```

---

### Step 2 - world_channel.py: include both new request classes

In world_channel.py: resolve the conflict by keeping `WRecComplete` (HEAD) and appending `WRecInteract` (main) - both classes are self-contained with no overlap.

---

### Step 3 - mission.py: merge all new methods, keep HEAD's to_prompt signature

In mission.py: resolve the conflict block by including methods from both sides in this order:

1. `active_focus()` - from HEAD
2. `advance()` - from HEAD
3. `record_action_success()` - from main
4. `record_action_failure()` - from main
5. `is_terminal()` - from main
6. `to_prompt(self, *, top_prompt: bool = True, focus: Mission | None = None)` - HEAD's signature (superset of main's; the shared method body immediately below the conflict already references the `focus` parameter, so main's narrower signature would break it).

---

### Step 4 - world_runner.py: keep judge_complete(), adopt WResBuild return type

In world_runner.py: resolve the conflict block by:

1. Keeping `judge_complete()` (HEAD) in full, immediately before `add_building()`
2. Using `-> WResBuild` as the return type for `add_building()` (from main)

---

### Step 5 - player.py conflict 1: combine lifecycle check with focus-aware think()

In player.py, around the `play()` loop: take the mission lifecycle management from main and the focus-passing call from HEAD:

```python
if self.mission.status == MissionStatus.PENDING or self.mission.is_terminal():
    new_obj = await self._generate_mission_objective()
    self._start_new_mission(new_obj)
alg.log(f"PLAYER.play {self.name}: needs to do {self.mission}")
action = await self.think(focus=self.mission.active_focus())
```

`is_terminal()` is now available from Step 3. `Player.think()` (the player-level wrapper around `PlayerBrain`) already accepted a `focus` parameter on `feat/action_focus` and was not conflicted, so no change there is needed.

---

### Step 6 - player.py conflict 2: dispatch both ActionComplete and ActionInteract

In player.py, in the action `match` block: include both case arms:

```python
case ActionComplete() as act:
    wrsp = await self.complete(act)
case ActionInteract() as act:
    wrsp = await self.interact(act)
```

---

### Step 7 - player.py conflict 3: keep complete(), adopt WResMove return type

In player.py: resolve the last conflict block by:

1. Keeping the full `complete()` method (HEAD) before `move()`
2. Updating `move()` return type annotation to `-> WResMove` (from main)

---

### Notes

1. **`is_terminal()` vs ActionComplete interaction**: `record_action_success()` and `record_action_failure()` (from main) target build/craft action outcomes; `complete()` (from HEAD) targets the explicit LLM-issued `ActionComplete` signal. These serve distinct code paths and can coexist without conflict.

2. **`interact()` implementation**: `player.py` imports `WRecInteract` and `WResInteract` in its import block (already merged, no conflict), and Step 6 dispatches to `self.interact()`. Confirm `interact()` is defined somewhere in `player.py` below the visible conflict range before finalising; if absent, it needs to be added.

3. **Mission fields `consecutive_failures` / `max_failures`**: `record_action_failure()` references these. The field definitions are above the conflict region in `mission.py` and should already be present from main's commits. Verify after resolution.

4. **`to_prompt()` call sites**: After Step 3, `to_prompt()` gains the optional `focus` keyword. All existing callers that omit it remain valid (default is `None`). No other files need updating.

5. **Verification**: after resolving all conflicts run `uv run pytest && uv run ruff check . && uv run pyright`.
