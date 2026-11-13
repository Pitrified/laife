---
status: done
---

# Phase 2 - A turn limit on the player loop

## Overview

Let a run end by itself.
Context: [`00_start.md`](00_start.md) Q4.

## Plan

- `Player.play(max_turns: int | None = None)`: the loop returns after turn `max_turns`; `None` keeps the live game's endless loop.
- `WorldRunner.simulate()` is unchanged. Whoever gathers the tasks cancels it once every player task has returned;
  a player waiting on a world response keeps the runner needed until then, so it is cancelled last.
- A player that has returned still answers messages:
  `WorldRunner` calls the target's `receive_message()` directly, outside the target's `play()` (read 2026-11-12).

## Done when

- A unit test drives `play(max_turns=...)` with the fake from phase 3, or with the turn body stubbed if phase 3 is not in yet.
- `make check` passes.

## Outcome

- `Player.play(max_turns=None)` loops while `max_turns is None or self.turn < max_turns`.
- `test_play_returns_at_max_turns` in `tests/entities/test_player_lifecycle.py`; without the change it fails (`play()` takes no `max_turns`).
- Cancelling `WorldRunner.simulate()` after the players return is the headless entry's job, in phase 4.
