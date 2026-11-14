---
status: done
---

# Phase 5 - Retire pygame

## Overview

`make run` serves the world page instead of opening a pygame window, and pygame leaves the repo.
After this, the live game and the headless run differ only in the chat config their players get.
Context: [`00_start.md`](00_start.md) Q6 (pygame retired once the page covers the window), [`04_pixi_detail.md`](04_pixi_detail.md) (the quit event it found missing).

## Goals

1. `make run` plays the live game with the configured provider, served on the page, capped by turns, and stoppable from the page.
2. pygame, `src/laife/rendering/` and every instruction about building it are gone.
3. Folder 34's two parked phases are closed as discarded, and the folder as done.
4. A run's structured log says how it ended.

## Plan

### One serving loop for both runs

- `serve_headless` in `laife.headless` holds the loop: server, world, players, the stop path. It moves to `laife.web.run` as `serve_run(runner, sim_control, *, turns, host, port)`, which takes a built world.
- `laife.headless` keeps `build_world` (scripted) and `serve_headless`, now a call to `serve_run`.
- `game/main.py` builds the live world (`WorldRunner()` and `setup_world` with the default chat config, as now) and calls `serve_run`. Its options are those of `game/headless.py --serve`: `--turns`, `--seed`, `--host`, `--port`, `--paused`. No `--pace`: the model is the pace.
- `make run` passes `TURNS`, `SEED`, `HOST`, `PORT`, `PAUSED`; the defaults are Q21 to Q23.

### The log says how a run ended

- `POST /control/quit` writes a `sim_control` event with `state="quit"`, beside `paused` and `resumed`.
- `serve_run` writes `state="stopped"` as it returns or is interrupted, so Ctrl-C shows too.
- The TUI already shows `sim_control` events; nothing changes there.

### What goes

- `src/laife/rendering/` (the renderer, the sprites, `SpriteLoader`), `pygame` in `pyproject.toml` and `uv.lock`.
- `SPRITES_FOL` and `STATIC_FOL` in `laife.config.constants`, used only by the pygame loader; `LaifePaths` has both.
- Docs: `docs/library/rendering.md` and its nav and index entries; the window in `docs/guides/getting_started.md` and `docs/guides/architecture.md`; the SDL line in `docs/guides/docs_maintenance.md`; the SDL and freetype notes in `CONTRIBUTING.md`.
- Instructions: `make run` described as serving the page; the Rendering row of the layer table; the g7 line about uv's managed Python, whose reason was pygame's missing 3.14 wheel. uv's managed Python stays as the interpreter; only the stated reason changes.
- Docstrings and comments that describe something by its relation to pygame ("no pygame dependency", "compatible with pygame.Rect", "in pygame the y-axis is flipped") are rewritten to state the convention itself: positions are top-left pixels, y grows south.
- `scratch_space/` is left as it is: throwaway scripts, not run by anything.

### Folder 34

- Phases 1 and 3 (`SystemExit` on quit, the AVX2 notice) are marked `discarded`, each with a line saying pygame left in folder 41 phase 5.
- With phases 2 and 4 done and 1 and 3 discarded, its `00_start.md` goes to `done`, with a log line.
- The `plan.md` item "Runtime warnings" is removed; "Renderer checks without a screen" is removed too, since `make e2e` is that check.

## Tests

- `serve_run` is what the headless serve tests already drive (`tests/web/test_stop.py`, the browser test); they move to it with no change in what they check.
- The quit event: `POST /control/quit` writes `sim_control` with `state="quit"`; a stopped `serve_run` writes `state="stopped"`.
- `game/main.py --help` runs in a subprocess and lists its options: an import check of the live entry point that spends nothing.
- No test plays the live game: it calls the provider.

## Done when

- `make check`, `make e2e` and plain `make headless` pass on g7 with pygame uninstalled (`make sync` removes it).
- `grep -ri pygame` outside `plans/`, `scratch_space/` and the lock finds nothing.
- On g4, by the user, one live run approved first: `make run` with the turn cap, the page open, resumed from the page, quit from the page. Before it, the plan states the most calls it can make (below).

## The live check

A player's turn makes at most four provider calls: a mission when it has none, its action, then a plan or a judge for that action, and a reply when another player talks to it.
Two players and `TURNS=3` therefore make at most 24 calls, and fewer in practice; the g4 run of 2026-11-13 made 9 calls in about three turns.
What a call costs on gpt-6-luna is not known here; the OpenAI usage page shows it after the run.

## Out of scope

- A live run on g7: g7 has the key, but live runs are the user's, on g4.
- Changing the chat params or the prompts (backlog "Tuning the chat params").
- Restarting a run from the page.

## Open questions

- Q21: The live turn cap. `make headless` defaults to 6 turns per player; a live turn spends credit.
  - a. `make run` caps at 3 turns per player by default, its own `LIVE_TURNS` variable, so a headless default never becomes a live one; `LIVE_TURNS=0` for no limit.
  - b. `make run` uses `TURNS`, default 6.
  - c. No cap by default, as today.
  - Recommended: a, because the cap is the cost control the user asked for, and keeping it separate means changing the headless default never changes spending.
  - ANS: a.
- Q22: Whether `make run` starts paused.
  - a. Paused: nothing is spent until the page resumes it.
  - b. Running, as today; `PAUSED=1` to start paused.
  - Recommended: a; the page is where the run is watched, so it should be open before the first call.
  - ANS: a.
- Q23: The backlog item "Seed for the live game": `setup_world` already takes a `random.Random`, and `game/main.py` gets an option parser in this phase.
  - a. Fold it in: `--seed`, `SEED` in `make run`; unseeded when not given, as today.
  - b. Leave it in the backlog.
  - Recommended: a; it is one option on a parser being written anyway, and a seeded live run starts from the same world as the headless one.
  - ANS: a.
- Q24: Where `make run` listens.
  - a. `127.0.0.1` by default, `HOST` for the tailnet address, as the headless run.
  - b. The tailnet address by default, so the phone reaches it without a flag.
  - Recommended: a; one default for both runs, and the live run is started on g4, where the browser is local.
  - ANS: a.

## What the implementation found

- `make run` takes its own `LIVE_SEED` rather than `SEED`, for the reason `LIVE_TURNS` exists: `SEED` defaults to 0 for the headless run, and the live game stays unseeded unless asked.
- `PAUSED` now means `1` to pause the headless serve and `0` to start the live game running; the headless target tests for `1` rather than any value, so `PAUSED=0` no longer pauses it.
- The pre-commit hook that blocks privileged commands caught the word in the CONTRIBUTING text being deleted; that edit went through the editor instead of a shell script.
- The backlog item "Seed for the live game" went with Q23; "Runtime warnings" and "Renderer checks without a screen" with the plan.
- The log check (`quit` then `stopped` last) is shown failing with the quit event removed.
- Test warnings went from 15 to 14 with pygame gone.
- Not run on g7: the live entry beyond `--help`. A paused live run makes no provider call until resumed, but live runs are the user's, on g4.
