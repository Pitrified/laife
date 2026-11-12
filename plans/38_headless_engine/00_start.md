---
status: in progress
priority: 0
description: |
  Run the real engine with no window and no provider: players fed by a scripted LLM, the structured log written to `cache/` as in a live run, usable by an agent and as a gate.
---

# headless engine - bootstrap

Picked from the `plan.md` backlog item "Headless run with a scripted LLM", whose text was:

> Run the real engine with no window and no provider: players fed by a scripted or recorded LLM, the structured log written to `cache/` as in a live run.
> It is the evidence the instructions ask for while planning and implementing, usable as a gate, and the thing an unattended session cannot do today.
> Open: recorded responses or a rule-based fake; whether `WorldRenderer` is skipped or pointed at SDL's dummy video driver.

## Why

The instructions treat the engine running as the evidence that a game change works.
Today the only run is `make run`: a pygame window and a paid provider call per chain step, so it needs the user.
An agent session on g7 has no `DISPLAY` and should not spend provider money, so it cannot produce that evidence at all.

## What the code offers

Read on 2026-11-12, on `main` after the folder 36 merge.

- **One chat config feeds every chain.**
  `Player.__init__` builds the brain, planner, replier and mission generator, and `WorldRunner.__init__` builds the build, craft and complete judges,
  all from `get_laife_params().llm_services.chat.default`.
  Replacing that one value before the runner and players are built swaps the provider for the whole game.
- **llm-core already has a fake.**
  `llm_core.testing.FakeChatModelConfig` builds a `FakeChatModel` that answers `with_structured_output` by parsing canned JSON.
  It cycles one response list regardless of the schema asked for,
  so it cannot serve a game where one config is shared by chains with five different output models
  (`ActionEnvelope`, `WorldJudgeResult`, `PlayerPlannerResult`, `PlayerReplyOutput`, `MissionGeneratorResult`).
  What is needed is a fake that picks its answer by schema.
- **The simulation has no pygame dependency.**
  No module under `src/laife/entities/` or `src/laife/config/` imports pygame; the mentions there are docstrings.
  `WorldRenderer` is the only display code, and `game/main.py` gathers it beside `runner.simulate()` and the players.
- **Nothing ends a run.**
  `Player.play()` and `WorldRunner.simulate()` loop forever; a run ends when the window closes.
- **Runs are not reproducible.**
  `setup_world()` in `game/main.py` places players with unseeded `random.randint`.
- **The structured log is already there.**
  `configure_logging()` writes `cache/game_<stamp>.jsonl` relative to the working directory, and `make tui` reads the newest one.
- **No recorded runs on g7.** `cache/` holds no `game_*.jsonl` here.
- **No embeddings or vector store at play time.** Nothing in `src/laife` outside `params/llm_services/` builds them.

## Proposed shape

Written as proposals before the planning round; the answers are under Questions.

- **Rule-based fake, not recorded responses.**
  Replay diverges as soon as the world differs from the recording (positions, a rejected build), there are no recordings on g7,
  and a rule set can be written to walk every branch of `Player.play()`'s action `match`.
  Recorded replay can be added later on the same seam if a case needs it.
- **A schema-dispatching fake chat model.**
  `with_structured_output(schema)` returns a runnable that asks a policy for an instance of `schema`.
  The model and config are general and could live in llm-core beside `FakeChatModel`; the policy is laife's.
- **Skip the renderer.**
  The headless entry gathers `runner.simulate()` and the players only.
  The SDL dummy driver would also exercise `WorldRenderer`, which is display code with nothing to verify without a screen.
- **A turn limit on the player loop**, so a run ends by itself and the gate terminates.
- **A seed**, so two runs of the same script produce the same log.
- **`setup_world()` moves out of `game/main.py`** into the package, so `make run` and the headless entry build the same world.
- **`make headless`** runs it and leaves the log in `cache/` for `make tui`;
  a pytest runs a short game and checks the log, which puts it in `make check`.

## Questions

Also agreed 2026-11-12: a seed for repeatable runs, and moving `setup_world()` into the package.

### Q1 recorded or rule-based

Proposed: rule-based, for the reasons above.

ANS 2026-11-12: rule-based.

### Q2 how much the policy reads

A policy that ignores the prompt and cycles the action types per player is short and deterministic, and covers every branch of the turn loop.
A policy that reads the rendered prompt (positions, nearby players) acts more like a player and breaks whenever a prompt version changes its wording.
Proposed: cycle, with a fixed script per player; the target of `ActionInteract` is the other player's name, known from the setup.

ANS 2026-11-12: cycle, with a fixed script per player.

### Q3 where the fake model lives

In laife first, under `src/laife/llm/` or a `testing` subpackage, and offered to llm-core once it has settled.
Putting it in llm-core now means an llm-core release and a tag bump in laife's `pyproject.toml`, which is a dependency change.

ANS 2026-11-12: in laife.

### Q4 how a run ends

Options: a `max_turns` argument on `Player.play()`; or the headless entry watches the players' `turn` and cancels the gather.
Proposed: `max_turns` on `play()`, `None` for the live game, and `WorldRunner.simulate()` cancelled once every player has returned.

ANS 2026-11-12: `max_turns` on `play()`.

### Q5 renderer skipped or SDL dummy

Proposed: skipped (above).

ANS 2026-11-12: skipped for now.
Checks of the actual rendering are a renderer concern, not the world's, and went to the `plan.md` backlog.

### Q6 what the gate asserts

A short game (two players, a few turns each) under pytest, then on the log:
every player reached the turn limit, every action type in the script appears, no error event.
It has to stay within a few seconds to stay in `make check`.

ANS 2026-11-12: the gate checks a minimal run, not deep integration, for now.
Headless mode is built for development, so the engine can be run and its log read while working; the test only keeps that run from breaking.
So: the run ends, every player reached the turn limit, no error event. Which actions appear is not asserted.
