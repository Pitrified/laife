---
status: done
---

# Phase 1 - struct log analysis

## Overview

Catalogue what the structured sink already emits so the UI knows what to filter
and group on. The JSON-lines sink already exists (`configure_logging()` in
`src/laife/meta/logger.py`); this phase is inventory and gap-finding, not new
plumbing. Context: [`00-start.md`](00-start.md).

## Goals

1. A complete catalogue of event types and their per-event payload fields.
2. The natural filter axes the UI will offer.
3. A decision on the missing fields needed to reconstruct one interaction.

## Plan

- Inventory event types from `src/laife/meta/log_events.py`: `action`,
  `world_response`, `mission_transition`, `llm_call`, `llm_result`,
  `world_request`. Note every record also carries loguru's `time`, `level`,
  `message`, and that `world_request` is `DEBUG` while the rest are `INFO`.
- Map per-event payload (the fields passed to `slog.bind(...)`):
  - `action`: `player`, `action`
  - `world_response`: `player`, `kind` (build/craft/...), `status`
  - `mission_transition`: `player`, `to_status`
  - `llm_call`: `model`, `elapsed`
  - `world_request`: `kind` (request class name)
- Identify filter axes: **player**, **event type**, **status**, **time**. Note
  that `world_request`/`llm_call` lack `player`.
- Decide on correlation: there is no id tying `llm_call` -> `action` ->
  `world_request` -> `world_response`, and no tick/turn number. Decide whether
  to add a `request_id` / `turn` field at the bind sites.
- Check for PII/secret leakage in serialized records before any UI renders them.

## Out of scope

- Changing the bind sites / adding new fields (decision only here; the edit, if
  agreed, lands when the consuming UI needs it).
- Building any renderer (phase 2).

## Done when

- The catalogue above is recorded (in this file or a short doc) and confirmed
  against the live `.jsonl`.
- A go/no-go decision exists on adding correlation id + turn number.

## Outcome

Go, and implemented (this phase grew from "decide" to "decide and land it" -
the decision was unambiguous and the edit was small and centralized). Final
catalogue, superseding the draft above:

- Event constants (`src/laife/meta/log_events.py`): `action`, `world_response`,
  `mission_transition`, `llm_call`, `world_request`. `llm_result` was listed in
  the original draft but nothing ever emitted it - removed as dead code.
- All five now log at `INFO` (`world_request` was the odd one out at `DEBUG`,
  invisible under the default log level - fixed).
- Per-event payload, now uniform: every event carries `player` and `turn`.
  - `action`: `player`, `turn`, `action_type` (the action class name, e.g.
    `ActionBuild` - added in phase 4; `str(action)` alone drops it), `action`
    (the full field string)
  - `world_response`: `player`, `turn`, `kind` (response class name, e.g.
    `WResBuild` - now emitted for all six request kinds, not just build/craft),
    `status`
  - `mission_transition`: `player`, `turn`, `to_status`
  - `mission_start`: `player`, `turn`, `from_status`, `objective` (added in
    phase 5; emitted by `_start_new_mission` so the generated mission objective
    reaches the log - pairs by `(player, turn)` with the `stage=mission`
    llm_call that produced it)
  - `llm_call`: `player`, `turn`, `model`, `elapsed`, `stage`
    (`action`/`plan`/`reply`/`mission` - added in phase 4). Emitted from four
    call sites, not just the brain: the action-picker (`stage=action`), the
    planner (`plan`), the replier (`reply`), and the mission generator
    (`mission`), all via `logger.timed_llm_call`.
  - `world_request`: `player`, `turn`, `kind` (request class name, e.g.
    `WRecBuild`, pairs with the matching `WRes*` on `world_response`)
- Correlation decision: **go**. Chose `(player: str, turn: int)` over a
  `request_id`/UUID - `Player.play()` already runs one full
  think -> act -> respond -> mission-update cycle per loop iteration
  sequentially, so a per-player monotonic `turn` counter is a natural,
  zero-infra correlation key. Stamped once in the single choke point every
  world round trip already passes through, `Player._world_request()`
  (`src/laife/entities/player.py`), and threaded into `PlayerBrain.think()`
  for `llm_call`. `(player, turn)` now ties `llm_call` -> `action` ->
  `world_request` -> `world_response` -> `mission_transition` together for
  one turn - verified manually against a real `cache/game_*.jsonl`.
- PII/secret check: none - this is a sandboxed simulation with synthetic
  players, no real user data ever enters the log.
- Landed in commit `f7411a3` ("Add player/turn correlation to the structured
  log"), full test/lint/typecheck suite green.
