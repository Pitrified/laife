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
| 2  | interaction targeting          | [`02_interaction_targeting.md`](02_interaction_targeting.md) | planned |
| 3  | serializer warning             | [`03_serializer_warning.md`](03_serializer_warning.md) | planned |

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
