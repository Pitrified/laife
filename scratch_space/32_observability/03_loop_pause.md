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

## Plan

- Add a shared pause flag / `asyncio.Event` that the world runner and player
  tasks check before advancing a step (e.g. `await pause_event.wait()` gating
  the top of the run loop). In-flight LLM calls finish, then everything blocks.
- Wire a trigger:
  - pygame in focus: watch a `KEYDOWN` (e.g. space) in the event pump, toggle
    the flag; or
  - decoupled inspector (Textual/web): expose pause/resume/step there and set
    the same flag via a small control queue (or an endpoint for the web case).
- Add **single-step**: clear the event, let one step run, re-set it. This is
  what makes the log readable - advance one interaction, read it, advance.
- Emit a `paused`/`resumed` marker event so the pause shows on the timeline.

## Out of scope

- Time-travel / rewind of past state (the log gives history; this is live
  control only).

## Done when

- The sim can be paused and resumed without losing in-flight work.
- Single-step advances exactly one interaction.
- Pause/resume is visible in the struct log.
- Project verification suite passes for any source changes (`uv run pytest &&
  uv run ruff check . && uv run pyright`).
