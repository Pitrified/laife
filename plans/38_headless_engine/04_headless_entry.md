---
status: planned
---

# Phase 4 - Headless entry and the minimal gate

## Overview

Wire phases 1-3 into a run an agent can start, and keep it from breaking.
Context: [`00_start.md`](00_start.md) Q5, Q6.

## Plan

- `game/headless.py`: configure logging, build the runner with the scripted chat config, `setup_world()` with a seeded `random.Random`,
  gather `runner.simulate()` and every `player.play(max_turns=...)`, cancel the runner when the players return. No `WorldRenderer`, no pygame import.
- `make headless`, with turns and seed overridable (`make headless TURNS=10 SEED=1`); the log lands in `cache/` and `make tui` opens it.
- The gate, a pytest in `make check`: a short run (the two players of `setup_world()`, a few turns) ends without an exception,
  every player reached the limit, and the log file holds an `action` event per player turn.
  No assertions on which actions happened: headless mode is for development, the test only keeps the run working.
- Docs: a short page under `docs/guides/` on running headless and reading the log; `copilot-instructions.md` "Running the engine" updated to name `make headless` and what it does not cover (rendering, real model behaviour).

## Done when

- `make headless` run here on g7, the log read back with `make tui` or by hand, and what it showed reported.
- The gate shown failing once (e.g. a script entry that raises), then passing.
- The gate adds seconds, not tens of seconds, to `make check`.
- `make check` passes.
