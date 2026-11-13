---
status: done
---

# Phase 4 - chain wrappers

## Overview

Use llm-core's `StructuredLLMChain` directly instead of the five laife wrappers. Context: [`00_start.md`](00_start.md), Q1 and Q5.
After phase 3 the four player chains are built inside `PlayerBrain`; the three judges are built in `WorldRunner.__init__`.

## What the code shows

- The wrappers and where they are built:
  - `ActionPicker` (`entities/action.py`): built by the brain; `ainvoke` unwraps `ActionEnvelope.act`.
  - `PlayerPlanner`, `MissionGenerator` (`llm/`): built by the brain from a `*Config`; `ainvoke` takes domain objects and builds the input with a private `_build_input`.
  - `PlayerReplier` (`llm/`): built by the brain from a `*Config`; `ainvoke` takes the input model.
  - `WorldActionJudge` (`entities/world_judge.py`): `WorldRunner` loads three prompts and builds `build_judge`, `craft_judge`, `complete_judge`; `judge_and_build`, `judge_craft`, `judge_complete` call `ainvoke(WorldJudgeInput(...))`.
- Every wrapper also has a sync `invoke`; nothing in `src` calls one.
- Each module also holds the chain's input and output models; `laife.llm.scripted_chat` imports the output models from there to answer by schema.
- Each input model repeats a docstring paragraph on the prompt variable validation; `docs/guides/llm_chains.md` explains the same rule and says "the input classes carry a note".
- Tests on the wrappers:
  - `test_player_planner.py`, `test_mission_generator.py`, `test_world_judge.py`: config instantiation, prompt validation at construction (raises on a missing variable, accepts a complete prompt), `invoke`/`ainvoke` forwarding.
  - `test_structured_chain.py` tests llm-core's `StructuredLLMChain` itself: validation, `invoke`/`ainvoke`, wrong output type.
- The game's real prompts are already validated against their input models in the suite: `test_player_brain.py` builds a brain from them, and `test_scripted_chat.py` builds a `WorldRunner`; `make headless` builds all of them.

## Proposed shape

- `PlayerBrain` holds four `StructuredLLMChain[...]` attributes: `action_chain`, `plan_chain`, `reply_chain`, `mission_chain`, each built from its `PromptLoaderConfig` with `PromptLoader(...).load_prompt()` (Q5).
- The input building of the planner and mission wrappers moves into `brain.plan` and `brain.propose_mission`; `brain.next_action` unwraps `.act`.
- `WorldJudge(config: WorldJudgeConfig)` replaces `WorldActionJudge` in `entities/world_judge.py` (Q14): three `StructuredLLMChain[WorldJudgeInput, WorldJudgeResult]` attributes `build_chain`, `craft_chain`, `complete_chain`, and `check_build`, `check_craft`, `check_complete` taking plain values and building the `WorldJudgeInput`.
- `WorldRunner.__init__` builds `self.judge` from its `chat_config` argument; `judge_and_build`, `judge_craft`, `judge_complete` keep the collision check, the state change and the `WRes` mapping, and call the judge.
- Removed: the five wrapper classes, `PlayerPlannerConfig`, `PlayerReplierConfig`, `MissionGeneratorConfig`, and the sync `invoke`s.
- The input docstrings become one line each; the validation rule stays stated once in `docs/guides/llm_chains.md`, rewritten to not point at the notes.
- Brain and judge tests mock the chain attributes, as in phase 3, asserting the input each chain receives and the result returned; a mocked `action_chain` returns an `ActionEnvelope`.
- Runner tests mock `runner.judge` methods instead of `runner.build_judge.ainvoke`.
- llm-core: the wrong-output-type case is added to its `tests/chains/test_structured_chain.py`, and a patch release is tagged at the end of the phase; laife's `pyproject.toml` moves to that tag (Q12). The tag and the push are the user's.
- `docs/library/llm.md`, `docs/library/entities.md` and the chains guide describe the modules as holding the models, not the chains.

## Questions

### Q10 where the models live

Proposed: each module keeps its input and output models under its current name (`llm/player_planner.py`, `llm/mission_generator.py`, `llm/player_replier.py`, `entities/world_judge.py`, `entities/action.py`).
That is the smallest diff, and `scripted_chat` and the tests keep their imports.
The alternative is one module for all chain models; the names `player_planner` and `world_judge` would then no longer name a class.

ANS 2026-11-13: leave the files as they are.

### Q11 the wrapper tests

Proposed: drop the tests of wrapper construction, validation and forwarding; keep the tests of the input and output models (`test_generator_input_fields`, the judge result and `WResStatus` tests, the `WRec*` tests in `test_world_judge.py`).
Validation of the real prompts stays covered by building the brain and the runner from them; the planner `Player.plan` tests stay where they are.

ANS 2026-11-13: drop them.

### Q12 `test_structured_chain.py`

It tests llm-core's class from laife. Proposed: delete it, since llm-core's own suite is where that class is tested.
llm-core's `tests/chains/test_structured_chain.py` covers validation (missing and extra variables), the lazily built chain, and `invoke`/`ainvoke`.
It has no case for a model returning the wrong output type, which laife's `test_invoke_raises_on_wrong_type` and `test_ainvoke_raises_on_wrong_type` cover; that case would move to llm-core, not stay here.

ANS 2026-11-13: delete it here and move the missing case to llm-core; any llm-core change this phase needs is fine, with a patch release at the end of the phase so laife pins a tag.

### Q13 timing the judges

The judges are the one LLM call with no `llm_call` record.
Proposed: leave it to the backlog item on timing in the chain, which would cover them without a call-site wrapper; this phase changes no behaviour.

ANS 2026-11-13: ok, as proposed.

### Q14 a judge class beside the runner

Asked by the user: split the judging out of `WorldRunner`, as the brain was split out of `Player`.

What it would be: `WorldJudge(config)` in `entities/world_judge.py`, replacing `WorldActionJudge`.
`WorldJudgeConfig` holds `chat_config` and one `PromptLoaderConfig` per judge (build, craft, complete).
It holds the three chains and has three async methods taking plain values and returning `WorldJudgeResult`:
`check_build(building, observation, player_state)`, `check_craft(utensil_name, description, observation, player_state)`, `check_complete(objective, outcome, observation, player_state)`.
The `action_details` strings, built today in the runner, move into these methods.
`WorldRunner` builds `self.judge` in `__init__` (its `chat_config` argument stays) and keeps `judge_and_build`, `judge_craft`, `judge_complete`: the collision check before the paid call, adding the building, mapping the verdict to a `WRes`.

Assessment, for:
- It is the same split as `PlayerBrain`/`Player`: the class holding the chains builds the input and returns the parsed result; the class holding the state applies it.
- The runner loses the prompt loading and the input strings, about 45 lines, and keeps the world rules.
- The judge's input building becomes testable without a runner, with the chains mocked as in the brain tests (Q9).
- It is the place where judge timing would go if the backlog timing item does not land in the chain (Q13).

Against:
- One more class and config; the runner keeps three thin methods that call it.
- It is not a pure wrapper, since it builds the input and holds three chains, so the "Done when" rule still holds.

Proposed: do it, inside this phase rather than as phase 5, since otherwise the runner gets three plain chains in this phase and loses them in the next.
Tests that mock `runner.build_judge.ainvoke` move to mocking `runner.judge.check_build`; `test_player_inventory.py` patches `runner.judge_craft` and is unchanged.

ANS 2026-11-13: yes, in this phase.

## Done when

- No class in `src/laife` only wraps a `StructuredLLMChain`; `WorldRunner` builds no chain.
- `make check` passes; `make headless` gives the same positions and the same `llm_call` records as before the phase.

## Decided by the agent while implementing

For the user's review, 2026-11-13.

- `WorldJudge` builds its three chains through one private `_chain(prompt)` helper, since they share the input and output models; the brain spells out its four, each on its own models.
- `check_build` takes the `Building` and formats it, as the runner did; `check_craft` and `check_complete` take the request's strings.
- `next_action` unwraps `.act` after the timed block, so the timing covers only the chain call.
- `test_world_judge.py` also lost its test of `MissingPromptVariablesError`'s message: it tests llm-core's class, which llm-core's suite matches by message. laife's test that the error is a `ValueError` went with `test_structured_chain.py` and was not moved.
- `tests/llm/test_player_planner.py` now holds only the `Player.plan` tests; the name is kept.
- The architecture table in `.github/copilot-instructions.md` still named `PlayerBrain.think()`, renamed in phase 3; the row now names `next_action()`.
- llm-core: the two wrong-output-type tests replace the built chain with a `RunnableLambda` returning a string; they set `_chain` with `# noqa: SLF001`, as the lazy-init tests in the same file do.

## Outcome

- The five wrappers, the three `*Config` models and the sync `invoke`s are gone; the chain modules hold only their models, with one-line input docstrings.
- `PlayerBrain` holds `action_chain`, `plan_chain`, `reply_chain`, `mission_chain` and builds the planner and mission input itself.
- `WorldJudge(WorldJudgeConfig)` holds `build_chain`, `craft_chain`, `complete_chain`, with `check_build`, `check_craft`, `check_complete`; `WorldRunner` builds `self.judge` and builds no chain.
- Tests: the wrapper tests and `tests/llm/test_structured_chain.py` are deleted; brain and judge tests mock the chain attributes and assert input and result; runner build tests mock `runner.judge.check_build`.
  The count went from 292 to 272: 17 wrapper and chain tests and the exception test removed, 4 judge tests added (a fifth replaces the chat-config check), and `tests/test_models_build.py` lost the three `*Config` cases and gained `WorldJudgeConfig`.
- `make check` passes. `make headless` with the default seed ends at the same positions; per player, the sequence of `llm_call`, action and world request records matches the run before the change.
  The turn stamped on a `reply` record is the replier's turn when the message arrives, so it follows the interleaving of the two players: one run after the change stamped both replies a turn differently, a second run matched the baseline exactly.
- Docs: the chains guide has a section on the world judge and no longer points at docstring notes; the llm and entities library pages and the glossary describe the modules as holding models.
- llm-core: the wrong-output-type case for `invoke` and `ainvoke` is in its suite, released as v0.3.1 with no library change.
  laife pins `@v0.3.1`; the lock moved only llm-core. `make check` passes and `make headless` ends at the same positions on it.
