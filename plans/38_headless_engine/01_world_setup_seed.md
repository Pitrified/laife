---
status: planned
---

# Phase 1 - Shared world setup with a seed

## Overview

Move `setup_world()` from `game/main.py` into the package, so the live game and the headless run build the same world, and make it repeatable with a seed.
Context: [`00_start.md`](00_start.md), "Also agreed".

## Plan

- New module `src/laife/entities/world_setup.py` holding `setup_world(runner, sim_control, rng)`, moved as is from `game/main.py`.
- The two player positions come from `rng.randint` instead of the module-level `random`, so the `noqa: S311` stays and the caller owns the seed.
- `game/main.py` imports it and passes `random.Random()`, unseeded: the live game behaves as today.
- A test builds the world twice with the same seed and gets the same player positions; with no LLM call involved, it needs no fake.

## Open

- Whether the live game takes a seed too (an env var or a CLI argument). Not needed for this folder; left out unless asked.

## Done when

- `make run` code path unchanged apart from the import (not run here: it needs a display and a provider).
- `make check` passes.
