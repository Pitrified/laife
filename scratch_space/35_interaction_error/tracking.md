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
| 1  | survive error responses        | [`01_survive_wres_error.md`](01_survive_wres_error.md) | planned |
| 2  | interaction targeting          | [`02_interaction_targeting.md`](02_interaction_targeting.md) | draft   |
| 3  | serializer warning             | [`03_serializer_warning.md`](03_serializer_warning.md) | draft   |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-07-11 : bootstrapped the folder from `32_observability/05.1_random_decisions.md`;
  traced the crash to the disagreement between `Player._world_request`'s fail-loudly
  type assertion and `route_interaction`'s documented `WResInteract | WResError`
  return; drafted phases 1-3.
