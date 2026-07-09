---
status: planned
---

# Phase 3 - pause / step the game loop

## Overview

To inspect state we need the simulation to hold still. The loop is
asyncio-driven (`world_runner.py` awaits on `input_queue`), not a pygame blit
loop, so "pause" means pausing async stepping, not just freezing the screen.
Best paired with the inspector from
[`02_textual_tui.md`](02_textual_tui.md). Context: [`00-start.md`](00-start.md).

## Goals

1. A pause/resume control that halts the sim before the next step.
2. A single-step control that advances exactly one interaction.

## Decisions

- **Pause unit = one player turn.** The natural "interaction" is one full
  iteration of `Player.play()` (observe -> think -> act -> respond -> mission
  update) - the same `(player, turn)` unit phase 1 stamped on every log event
  and phase 2's focus-turn groups. Gating at the top of `play()` means an
  in-flight turn (including its LLM calls and world round trip) always
  finishes before the player blocks, so nothing is lost or left half-done.
- **Do not gate `WorldRunner.simulate()`.** If the runner also paused, a
  player mid-turn awaiting its `world_response` would deadlock against the
  paused runner. The runner keeps servicing requests; it drains naturally
  once every player is blocked at the turn gate.
- **Trigger from pygame `KEYDOWN`, not from the TUI** (resolves the open
  question in `00-start.md`). TUI-driven control needs cross-process IPC
  (control file / socket / signal) from the inspector to the game - real
  machinery for no payoff yet, since watching the sim means the pygame
  window is already at hand and the renderer already has an event pump with
  `KEYDOWN` handling (`check_events()`). The pause markers land in the
  `.jsonl`, so the TUI still *shows* pause/resume/step without any wiring.
  Revisit IPC only if keyboard control proves insufficient.

## Plan

- New module `src/laife/entities/sim_control.py` with a `SimControl` class -
  pure asyncio, no pygame import (same discipline as `WorldRunner`):
  - Internally an `asyncio.Condition` over two fields: `running: bool`
    (starts `True`) and `step_permits: int` (starts 0).
  - `async wait_turn(player: str, turn: int) -> None`: returns immediately
    while running; while paused, waits until resumed or a step permit is
    available, consuming one permit if so. This is the only gate point.
  - `pause()` / `resume()`: flip `running`, notify waiters.
  - `step()`: increment `step_permits` by one, notify - exactly one blocked
    player advances one full turn, then re-blocks at its next `wait_turn`.
    (`asyncio.Condition` wakes waiters FIFO, so repeated steps alternate
    between blocked players roughly fairly; good enough for a dev control.)
  - `toggle()` convenience for the keybinding; `paused` property for display.
  - Each of pause/resume/step emits the marker event (below) via `slog`.
- **`src/laife/meta/log_events.py`**: add `EVT_SIM_CONTROL = "sim_control"`.
  One event name with a `state` field (`paused` / `resumed` / `step`) rather
  than three event constants - filters on the TUI's event axis stay short.
- **`src/laife/entities/player.py`**: `Player.__init__` gains
  `sim_control: SimControl | None = None` (default `None` keeps every
  existing test and stub constructor working - `wait_turn` is simply not
  awaited when absent). `play()` awaits
  `self.sim_control.wait_turn(self.name, self.turn)` at the top of the
  `while True:` loop, before `self.turn += 1`.
- **`src/laife/rendering/world_renderer.py`**: `WorldRenderer.__init__`
  gains `sim_control: SimControl | None = None`. `check_events()` adds two
  keys: `K_SPACE` -> `toggle()`, `K_n` -> `step()` (no-op unless paused).
  Show the state in the window caption (`set_caption("lAIfe simulation
  [PAUSED]")` on pause, restored on resume) so the freeze is visibly
  deliberate. The render loop itself never pauses - the screen stays live
  and the event pump keeps accepting keys while the sim is held.
- **`game/main.py`**: construct one `SimControl`, pass it to the renderer
  and to both players.
- **TUI follow-up (small)**: add `sim_control` to `EVENT_COLORS` (e.g.
  `red`) and a `_detail` branch showing `state=...`, so pause markers read
  clearly on the timeline.

## Out of scope

- Time-travel / rewind of past state (the log gives history; this is live
  control only).
- Driving pause/step from the TUI or any other process (needs IPC; see
  Decisions - revisit only if keyboard control proves insufficient).
- Pausing mid-turn (finer-grained gates inside `play()`); per-turn
  granularity is what the log correlates on.

## Testing

- Unit tests for `SimControl` (pure asyncio, same `asyncio.run(_run())`
  pattern as the rest of the suite):
  - `wait_turn` returns immediately while running.
  - After `pause()`, a task blocks at `wait_turn`; `resume()` releases it.
  - While paused, `step()` releases exactly one of two blocked waiters;
    a second `step()` releases the other.
  - pause/resume/step each emit `EVT_SIM_CONTROL` with the right `state`.
- A `Player`-level test that a stubbed player's `play` path blocks at the
  gate when paused is not worth the stubbing cost - the gate call is one
  awaited line; the `SimControl` tests carry the behavior.
- Manual smoke: `make run`, let a couple of turns land, press space -
  confirm the sim halts after in-flight turns finish while the window stays
  responsive; press `n` a few times and watch single turns land in the TUI
  (`make tui`), including the `sim_control` markers; space again to resume.

## Done when

- The sim can be paused and resumed without losing in-flight work.
- Single-step advances exactly one player turn.
- Pause/resume/step are visible in the struct log and readable in the TUI.
- Project verification suite passes (`uv run pytest && uv run ruff check . &&
  uv run pyright`).
