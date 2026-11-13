---
status: planned
---

# Phase 2 - timing in the chain

## Overview

Every `StructuredLLMChain` call reports its duration through a callback; laife writes the `llm_call` record from it, with player and turn taken from the log context. Context: [`00_start.md`](00_start.md), Q3 (A).

## Steps

llm-core:

- `StructuredLLMChain` gets two optional fields after the four existing ones: `name: str = ""` and `on_call: Callable[[str, str, float], None] | None = None`, called as `on_call(name, chat_config.model, elapsed_seconds)` after a successful `invoke` or `ainvoke`, after the output type check.
  A call that raises reports nothing, matching `timed_llm_call` today.
- Tests: called once with name, model and a non-negative elapsed for `invoke` and `ainvoke`; not called when the chain raises or the output type is wrong; no callback is fine.

laife:

- `laife.meta.logger`: `log_llm_call(name, model, elapsed)` writes the `llm_call` record with `stage=name`; `timed_llm_call` is removed.
  Player and turn are not arguments: they come from `slog.contextualize(player=..., turn=...)`.
- Where the context is set:
  - `Player.play`, around the body of each turn, with `self.name` and `self.turn` (covers mission, think, plan).
  - `Player.receive_message`, with its own name and turn: it runs in the world's task, where the requester's context is set.
  - `WorldRunner.simulate`, around `handle_player_input`, with the request's `player_name` and `turn` (covers the judges).
- `PlayerBrain`: chains built with `name` `action`, `plan`, `reply`, `mission` and `on_call=log_llm_call`; `player_name`, the `turn` arguments and `_timed` go. `Player` stops passing them.
- `WorldJudge`: chains named `judge_build`, `judge_craft`, `judge_complete`, same callback.
- Tests: the brain's timing test becomes a check that each chain carries its name and the callback; the judge gets the same; `test_logger.py` tests `log_llm_call` inside and outside a `contextualize` block; one test that a reply record carries the replier's name while the world handles the sender's request.
- Docs: `docs/guides/llm_chains.md` (timing paragraph), `docs/library/meta.md`; `plan.md` item "Timing every LLM call" removed.

## To check while implementing

- That a `bind` on `slog` wins over a `contextualize` value for the same key, so the existing records that bind `player` and `turn` themselves are unchanged.
  loguru builds `extra` as `{**core.extra, **context.get(), **extra}` (`_logger.py`, `_log`), so the bound value wins; a test pins it.
- That `contextualize` set inside a task does not leak into the others: each asyncio task runs in a copy of the context.

## Done when

- `make check` passes in both repos.
- `make headless`: same positions; the `llm_call` records for action, plan, mission and reply match the previous run on player, turn and stage; the judges now write `llm_call` records with the requester's player and turn.
