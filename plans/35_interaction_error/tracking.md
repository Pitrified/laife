# interaction weirdness - implementation tracking

A live run died with `TypeError: Expected WResInteract, got WResError` after the
LLM addressed a building (`'Big ol Farm'`) as an interaction target; a pydantic
serializer warning fired in the same run. Make error responses survivable, then
investigate the targeting and the warning. Analysis and decisions in
[`00_start.md`](00_start.md); original capture in
[`32_observability/05.1_random_decisions.md`](../32_observability/05.1_random_decisions.md).

## Key decisions

- Resilience before diagnosis: the game must survive a `WResError` no matter why
  the bad target was picked; the error becomes a turn outcome, not a crash.
- The targeting question (phase 2) is an investigation and may end in a design
  change (e.g. a building-interaction action), not necessarily a patch.

## Phases

| #  | Phase                          | Plan                                                | Status  |
| -- | ------------------------------ | --------------------------------------------------- | ------- |
| 1  | survive error responses        | [`01_survive_wres_error.md`](01_survive_wres_error.md) | done |
| 2  | interaction targeting          | [`02_interaction_targeting.md`](02_interaction_targeting.md) | done |
| 3  | serializer warning             | [`03_serializer_warning.md`](03_serializer_warning.md) | done |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-07-11 : bootstrapped the folder from `32_observability/05.1_random_decisions.md`;
  traced the crash to the disagreement between `Player._world_request`'s fail-loudly
  type assertion and `route_interaction`'s documented `WResInteract | WResError`
  return; drafted phases 1-3.
- 2026-07-11 : detailed all three phase plans (all now `planned`).
  Phase 1: seam decided - `_world_request` widens to `T | WResError` (the
  `play()` dispatch already funnels every response into history, and the
  mission-update isinstance guards pass errors through as neutral).
  Phase 2: planning-time code read showed the observation already labels
  entity types, so the leading hypothesis is a capability gap, not name
  confusion; plan is investigation + two cheap mitigations + a recorded
  steer/validate/extend fork. Only the fork's implementation depends on
  phase 1 landing and on live evidence - everything up to it is planned.
  Phase 3: `parsed` traced to langchain's `with_structured_output` envelope
  via llm-core (`structured_chain.py:91`); plan is warnings-as-errors repro,
  then fix at the right layer (llm-core is our own git-pinned package, so a
  fix there means tag + pin bump) or narrow suppression.
- 2026-07-11 : phase 1 done - `_world_request` widened to `T | WResError` and
  every helper short-circuits on error (`interact` returns it into history,
  `observe` keeps the stale observation, `complete` skips mission advance,
  `move` folds a step error into its `WResMove` error shape, `build`/`craft`
  widen types only). Fail-loudly `TypeError` kept for genuinely unknown types.
  No TUI change needed (detail builders already render `kind`/`status`).
  Deviation: no first-turn observe special case - the constructor always
  seeds `last_observation`. 6 new tests; 3 existing tests updated (one had
  asserted the old raise-on-WResError behavior). Suite green: 226 passed,
  ruff and pyright clean. See
  [`01_survive_wres_error.md`](01_survive_wres_error.md#outcome).
- 2026-07-11 : phase 2 advanced to the live-game boundary. Both cheap
  mitigations landed: tightened `ActionInteract.target_name` schema
  description, and a "Nearby players (valid interaction targets)" section in
  the new `player_brain/v3.jinja` fed by
  `WorldMapObservation.nearby_players_to_prompt()` via a new
  `nearby_players` field on `ActionPickerInput`. Found the classification
  sweep is blocked: `cache/` holds no `.jsonl` logs, so it needs fresh live
  sessions. Remaining (live game required): behaviour observation, target
  classification on new logs, and the steer/validate/extend fork decision.
  Suite green: 228 passed, ruff and pyright clean. See
  [`02_interaction_targeting.md`](02_interaction_targeting.md#progress-2026-07-11).
- 2026-07-11 : back on an LLM-connected machine; recorded the queued live
  work below. `cache/` now holds `.jsonl` logs (07-10, so **pre-mitigation** -
  baseline only, they cannot test whether the phase 2 mitigations helped).
  Baseline sweep already yields one data point: the only `ActionInteract` in
  them repeats the original pattern verbatim -
  `target_name='Big ol Farm' message='I would like to gather crops.'`,
  `reason='To gather crops...'` - a sensible building-directed intent, early
  evidence leaning toward the **extend** fork. Next steps, in order:
  1. Phase 3 (independent, cheapest, do first): minimal serializer-warning
     repro - drive one `ActionPicker.ainvoke` against the live backend with
     `warnings.filterwarnings("error", message=".*Expected .none.*")`, read
     the frame, fix at the right layer (llm-core tag+pin bump vs narrow
     suppression). Per [`03_serializer_warning.md`](03_serializer_warning.md).
  2. Phase 2 live runs: `make run` a few sessions on the v3 prompt
     (`version: auto` resolves to v3), watching whether the brain self-corrects
     after the phase 1 error line and the new target listing, or loops on the
     same building.
  3. Phase 2 classification: re-sweep `cache/game_*.jsonl` including the new
     post-mitigation sessions, classify each interact target (player /
     building / terrain / hallucinated), write up in `02_interaction_targeting.md`.
  4. Phase 2 fork decision: record steer / validate / extend with that
     evidence. If extend, draft `04_building_interaction.md` and add its row
     to the phases table. Baseline already tilts toward extend; confirm the
     mitigations didn't already reduce it to noise before committing.
  5. Run the verification suite (`make test lint typecheck`) and mark phases
     2 and 3 done.
- 2026-07-11 : phase 3 done. Live repro pinned the warning to pure
  langchain-openai internals (`chat_models/base.py:1540` `_create_chat_result`
  -> `response.model_dump()`; `parsed` field declared `Optional[None]` but
  holds our `ActionEnvelope`) - not our code, not llm-core chain construction,
  so no tag/pin bump. Fixed with narrow suppression: `_suppress_known_warnings()`
  in `meta/logger.py`, called from `configure_logging`, filtering the pydantic
  serializer `UserWarning` from `pydantic.main` only. Verified live (0 surviving
  hits over a real `ainvoke`, PASS); suite green 228 passed, ruff+pyright clean.
  Bonus phase 2 signal from the two live runs: with the v3 mitigations the brain
  picked `ActionInteract(target_name='p1')` (a player) and `ActionMove` under the
  "gather crops from the farm" mission with the farm in view - it did not address
  the building. Encouraging for the steer fork, but n=2; still needs the proper
  phase 2 live-run + classification pass. See
  [`03_serializer_warning.md`](03_serializer_warning.md#outcome-2026-07-11).
- 2026-07-11 : phase 2 done - fork decided STEER. Controlled live harness
  (`phase2_targeting.py`, real chain + real `WorldMapObservation`, N=5 over three
  building-tempting scenarios) plus the two earlier full-call samples: 0 building
  targets and 0 hallucinated targets across ~17 live samples. Key readings: with
  no valid player in range the brain moves rather than addressing the building or
  hallucinating a target (capability gap does not surface as a bad interact), and
  a farm-target `WResError` already in history makes the next pick redirect to the
  player 5/5. The mitigations + phase-1 error line drop the miss rate to noise, so
  no validation and no building-interaction capability are needed; extend is not
  scoped as a follow-up. No code change this step (mitigations landed last
  session); suite unchanged at 228 passed, ruff+pyright clean. Effort complete -
  all three phases done. Write-up:
  [`02_interaction_targeting.md`](02_interaction_targeting.md#evidence-and-decision-2026-07-11).
