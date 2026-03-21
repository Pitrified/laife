# Mission lifecycle (completion and failure)

Wire up mission status transitions: after the world judge confirms a build/craft succeeded, mark
the active mission `COMPLETED`. After N consecutive failures, mark it `FAILED` and start a new
mission. Without this, the player loops forever on a single mission.

## Why is FAILED state needed?

> wouldn't the player just re-plan after a failure and try again until it succeeds?

Re-planning on every failure works when failure is transient (wrong position, temporary obstacle).
But `FAILED` covers cases re-planning cannot fix on its own:

- **Stuck in a structural dead-end**: e.g. the LLM keeps picking `ActionBuild` but
  the world judge always rejects it (wrong terrain, missing resource in range). Without
  a failure ceiling the player burns LLM calls indefinitely on an impossible goal.
- **Corrupted mission context**: a sub-mission may have been created with a bad
  objective. N failures signal the parent to skip or replace it rather than retry forever.
- **Observable termination for parents**: in nested missions, `FAILED` propagates upward
  so the parent can replan with the knowledge that branch is unresolvable, instead of
  waiting for it to magically succeed.
- **Debuggability**: a terminal `FAILED` status in mission history is visible to both the
  LLM (context for the next mission) and the developer.

The key insight: a single failure is a signal to retry; N consecutive failures with no
progress is a signal the current goal is structurally broken. `FAILED` represents the
latter, `PENDING`/`ACTIVE` represents the former.

## Implementation plan

### 1. `Mission` model (`src/laife/llm/mission.py`)

- Add `MAX_MISSION_FAILURES = 5` module constant (default).
- Add `consecutive_failures: int = 0` and `max_failures: int = MAX_MISSION_FAILURES` fields.
- Add `record_action_failure() -> None`:
  - increments `consecutive_failures`.
  - sets `status = FAILED` when `consecutive_failures >= max_failures`.
- Add `record_action_success() -> None`:
  - resets `consecutive_failures = 0`.
  - sets `status = COMPLETED`.

### 2. `Player` play loop (`src/laife/entities/player.py`)

- Add `_update_mission_from_response(action, wrsp)`:
  - only build and craft responses affect mission status.
  - `WResBuild` / `WResCraft` with `SUCCESS` -> `mission.record_action_success()`.
  - `WResBuild` / `WResCraft` with `ERROR` -> `mission.record_action_failure()`.
  - other action types (move, plan, interact) are neutral.
- Add `_start_new_mission()`:
  - creates a new `Mission` with the same objective and `status = ACTIVE`.
  - resets `self.history`.
  - logs the transition.
- In `play()`, after adding the history entry:
  - call `_update_mission_from_response(action, wrsp)`.
  - if `mission.status` is `COMPLETED` or `FAILED`: call `_start_new_mission()`.

### 3. Tests

- `tests/llm/test_mission_lifecycle.py` - pure unit tests on `Mission`:
  - `record_action_success` sets `COMPLETED`, resets counter.
  - N `record_action_failure` calls sets `FAILED`.
  - fewer-than-N failures do not change status.
- `tests/entities/test_player_lifecycle.py` - integration tests on `Player`:
  - `WResBuild SUCCESS` marks mission `COMPLETED` and triggers new mission.
  - `WResBuild ERROR` x N marks mission `FAILED` and triggers new mission.
  - move errors do not affect mission status.
