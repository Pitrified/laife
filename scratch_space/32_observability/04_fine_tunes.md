---
status: planned
---

# Phase 4 - inspector fine-tuning

## Overview

Polish the inspector's signal-to-noise now that the live smoke (phases 1-3)
has surfaced concrete rough edges. Two workstreams: emission-side gaps
(events that are missing or under-described in the `.jsonl`) and render-side
noise (the TUI's `detail` column and row density). Grounded in the draft
notes below and confirmed against the code. Context:
[`00-start.md`](00-start.md), catalogue in
[`01_struct_log_analysis.md`](01_struct_log_analysis.md), the TUI in
[`02_textual_tui.md`](02_textual_tui.md).

Kept as one phase because the items are small and cohesive; split into a
follow-up only if the coverage audit (goal 3) turns up more than a handful of
missed events.

## Original draft notes

- Which action is picked: the `action` row shows the reason but not the
  action *type*.
- Less noise: `world_request` -> `world_response` pairs could collapse to one
  line; do `world_request`s ever carry a detail?
- More actions: e.g. getting a mission from the world - are some events
  missed?
- Final doc updates.

## Findings (grounded in code)

1. **Action type is invisible.** `Player.think` emits
   `event=action, action=str(action)` (`player.py:292`). `action` is a
   pydantic v2 `BaseAction`, whose `__str__` renders field values *without*
   the class name (e.g. `reason='build a hut' building_type='hut' size=3`),
   so the row shows the reason but never Build/Craft/Move/Plan/Complete/
   Interact. The TUI detail builder just forwards that string
   (`tui.py:45`).
2. **`world_request` carries no detail.** It binds only
   `player, turn, kind` (the request class name, `world_runner.py:102`); the
   matching `world_response` binds `player, turn, kind, status`
   (`player.py:313`). So a `WRec*`/`WRes*` pair is two rows that together say
   "this request kind, this status" - the request row adds nothing the
   response row lacks except ordering. Confirmed: `world_request` never has a
   payload beyond `kind`.
3. **Three LLM calls are unlogged.** Only the brain's action-picker emits
   `llm_call` (`player_brain.py:64`). The planner (`Player.plan` ->
   `planner.ainvoke`), the replier (`receive_message` -> `replier.ainvoke`),
   and the mission generator (`mission_generator`) each make a real LLM
   network call with no `llm_call` event - so their latency and model are
   invisible, and an `interact`/`plan`/mission-refresh turn shows a gap where
   the LLM time actually went. (World round-trips themselves are *not* a gap:
   `world_runner.simulate` logs `world_request` for every `WReq` and
   `_world_request` logs `world_response` for every round trip, so any
   request routed through those choke points is already covered.)

## Goals

1. **Surface the action type.** Add `action_type=type(action).__name__` at
   the `action` bind site and lead the TUI detail with it (e.g.
   `ActionBuild reason=...`). Keep `action` (the full string) as-is so
   nothing is lost.
2. **Collapse `world_request`/`world_response` noise.** Render-side only: in
   the TUI, coalesce a `(player, turn, kind)` request/response pair into one
   line (`WRecBuild -> WResBuild status=success`) rather than two rows. The
   `.jsonl` keeps both events; the collapse is a display concern so replay and
   focus-turn stay complete. Guard for an in-flight request whose response
   has not arrived yet (show the request alone, upgrade in place when the
   response lands).
3. **Close the `llm_call` gaps.** Emit `llm_call` (with `player, turn, model,
   elapsed`) from the planner, replier, and mission-generator call sites, the
   same shape the brain uses. Add a `stage`/`kind` field
   (`action`/`plan`/`reply`/`mission`) so the four are distinguishable. Watch
   the decoupling contract: `receive_message` runs inside the world loop and
   must not touch any asyncio queue - `slog.bind(...).info(...)` is safe
   (synchronous, no queue), same as the existing sites.
4. **Final doc pass.** Update the phase-1 catalogue
   ([`01_struct_log_analysis.md`](01_struct_log_analysis.md)) with the new
   `action_type` and `stage` fields and the four `llm_call` sources, and the
   phase-2 detail-column description
   ([`02_textual_tui.md`](02_textual_tui.md)) with the collapsed pair
   rendering, so the catalogue stays the source of truth.

## Out of scope

- Random warnings on quit / pydantic V1 / pygame AVX2
  ([`05_random_warnings.md`](05_random_warnings.md)) - spun out as a separate
  future cleanup, unrelated to the inspector (see tracking note).
- Any new event *types* beyond filling the `llm_call` gaps; no new columns.
- Reworking filters or bindings - unchanged from phase 2.

## Testing

- Emission (goals 1, 3): unit-test the new binds the way phase 1/3 events are
  tested - assert `action_type` appears on the `action` record and that the
  planner/replier/mission-generator paths each emit one `llm_call` with the
  right `stage`. Loguru sink capture as in the existing event tests.
- Render (goal 2): extend `tests/observability/test_tui.py` with a fixture
  `.jsonl` containing a request/response pair and assert the table shows one
  collapsed row; add a pair with a missing response and assert the request
  shows alone. Reuse the headless `App.run_test()` pilot.
- Full suite + `ruff` + `pyright` green, then a short live smoke
  (`make run` + `make tui`) to confirm the action type reads clearly and a
  plan/interact turn now shows its LLM latency.

## Done when

- An `action` row names which action was picked.
- A world round trip reads as one line in the TUI, without losing either
  event from the `.jsonl`.
- Planner, replier, and mission-generator turns show their `llm_call`
  latency, distinguishable by `stage`.
- The phase-1 catalogue and phase-2 detail description reflect the changes.

## Outcome

_(to be filled when the phase lands)_
