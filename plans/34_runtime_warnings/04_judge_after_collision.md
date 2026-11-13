---
status: done
---

# Phase 4 - Judge after the collision check

## Overview

`WorldRunner.judge_and_build()` calls the build judge, a paid LLM call, and only then `add_building()`, which checks collisions and appends in one step.
A build that collides pays for a judge call that cannot change the outcome.
Context: [`00_start.md`](00_start.md), backlog item "Judge after the collision check".

## Plan

- Split the collision loop out of `add_building()` into a check that returns the colliding `WResBuild` or `None`.
  `add_building()` keeps its behaviour for `setup_world()`, which calls it directly.
- `judge_and_build()`: collision check first, return its error without calling the judge; then the judge; then append.
- The feedback strings stay as they are.

## Done when

- A unit test: a colliding build returns the collision error and the judge is not called.
- A non-colliding build still goes through the judge.
- `make check` passes; `make headless` runs.

## Outcome

- `WorldRunner.check_building_collision()` returns the collision `WResBuild` or `None`; `add_building()` and `judge_and_build()` both call it.
- `judge_and_build()` checks collisions, then asks the judge, then appends.
- `test_judge_and_build_colliding_skips_judge` and `test_judge_and_build_free_spot_asks_judge` in `tests/entities/test_world_judge.py`.
  On the old order the first fails: the judge mock is called once.
- `make check` passes; `make headless` runs, both players' builds succeed.
