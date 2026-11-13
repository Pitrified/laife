---
status: planned
---

# Phase 1 - mechanical

## Overview

Two changes with no behaviour change. Context: [`00_start.md`](00_start.md).

## Plan

### `BaseModelKwargs`

- Import it from `llm_core.data_models.basemodel_kwargs` in the five chain modules and in `tests/llm/test_structured_chain.py`.
- Delete the `src/laife/data_models/` package: it holds only the re-export.
- Remove `docs/library/data_models.md`, its `mkdocs.yml` nav entry, and the `data_models` mentions in `docs/library/README.md`.

### World requests

- `WReq` and the six `WRec*` become `@dataclass(kw_only=True, eq=False)`.
  `eq=False` keeps comparison by identity, as today, and keeps requests hashable.
  A request is a one-off message with its own reply queue: two with the same fields are still two messages, each owed a reply, and nothing compares them.
  A field-based `__eq__` would be identity in practice, since each carries a different `response_queue`, and would walk into `WRecMove.player`.
- `player_name` and `turn` become `field(default="", init=False)` and `field(default=-1, init=False)`: `Player._world_request` sets them after construction, and nothing passes them to the constructor.
- The hand-written `__str__` methods go, and with them the `id(self)` they print; the structured log ties a request to its turn through `player_name` and `turn`, not the id.
  Two keep a custom string: `WRecMove`, because `Player` has no `__repr__` and the default would print `<Player object at ...>`; `WRecInteract`, because `sender_prompt` is a long text. Each prints names and short fields only.
- Every construction in `src` and `tests` already uses keywords; check that it still does after the change.

## Done when

- No `*args, **kwargs` forwarding and no `noqa: ANN002/ANN003` left in `world_channel.py`.
- `make check` passes with the same test count, including the strict docs build; `make headless` gives the same positions as on `main`.
