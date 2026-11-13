---
status: done
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

## Outcome

- The run logic is `run_headless(turns=, seed=)` in `src/laife/headless.py`, so the gate imports it; `game/headless.py` is the CLI and prints each player's turns and position and the log path.
  `configure_logging()` now returns the log path.
- `setup_world()` takes `chat_configs`, a map from player name to config; a map missing a player raises `MissingPlayerChatConfigError` rather than fall back to the paid default.
- Found while wiring it: `laife/entities/__init__.py` re-exported the sprites and `WorldRenderer`, so every `laife.entities` import loaded pygame. The re-exports are gone (nothing used them); `laife.headless` loads no pygame.
- Found by showing the gate failing: with the reply answer removed, the world task died on `UnscriptedSchemaError` inside `route_interaction` and the players waited on their world requests forever.
  `run_headless` now waits on the world and the players together and re-raises the world's exception.
  The live game does not have this hang: its `asyncio.gather` includes the world task and re-raises.
- The gate runs one pass of the default script (six turns per player) and asserts the turn counts, one `action` event per player turn, and no `world_response` with status error.
  Shown failing with the reply answer removed (`UnscriptedSchemaError`), then passing. The test call takes well under a second.
- `make headless` run on g7, twice with seed 3: both runs took the same actions with the same outcomes, every world response `success`, same end positions.
  The interleaving of the two players differed, and so did the turn stamped on one reply (a reply carries the receiver's current turn). `docs/guides/headless.md` says so.
- The log was read by hand, not with `make tui`: the TUI is interactive and an agent session has no terminal to drive it.
- Docs: `docs/guides/headless.md`, linked from the guides index and getting started; "Running the engine" in the instructions names `make headless`, what it does not cover, and that a new output model needs a scripted answer.
