---
status: planned
---

# Phase 3 - the thinking moves into `PlayerBrain`

## Overview

`PlayerBrain` becomes the player's thinking layer: it owns the four player chains, and `Player` asks it.
The mind state stays on `Player`. Context: [`00_start.md`](00_start.md), Q3.

## What the code shows

- `Player.__init__` builds four `PromptLoaderConfig`s from `paths.prompts_fol` and four chain objects: `brain` (`PlayerBrain`, around `ActionPicker`), `planner`, `replier`, `mission_generator`, all on one `chat_config`.
- The four LLM call sites in `Player`:
  - `think()`: sets `THINKING`, calls `brain.think(...)` with mission, history, observation, state, inventory, name and turn; logs `EVT_ACTION`; sets `IDLE`.
  - `_generate_mission_objective()`: times and calls `mission_generator.ainvoke(observation, state, inventory)`, logs the reason, returns the objective.
  - `plan()`: sets `THINKING`, times and calls `planner.ainvoke(mission, history, observation, state)`, then adds the sub-missions, advances the mission, resets the history, sets `IDLE`, returns `WResPlan`.
  - `receive_message()`: times and calls `replier.ainvoke(PlayerReplyInput(...))`, returns the reply. Called by `WorldRunner.route_interaction`; must not touch the world queue.
- The mission generator and planner wrappers build their input from domain objects inside `ainvoke`; the replier's input is built in `Player`; `PlayerBrain.think` builds the action input.
- Tests reaching into the chains: `test_player_planner.py` and `test_mission_step_runner.py` replace `player.planner` / `player.brain`; `test_player_interaction.py` replaces `player.replier`; `test_scripted_chat.py` reads the four `chat_config`s; `test_player_brain.py` replaces `brain.action_picker`.
- `laife.llm.scripted_chat` answers by output schema, and each chain builds its own model from the config, so only the action chain advances the script. That holds as long as the brain keeps one chain per call kind.

## Proposed shape

- `PlayerBrainConfig`: `chat_config` plus one `PromptLoaderConfig` per chain (action, plan, reply, mission), built in `Player.__init__` as today.
- `PlayerBrain(config, player_name)` holds the four chains and has four async methods, each taking plain values and returning the parsed result:
  - `next_action(mission, history, observation, player_state, inventory, turn) -> BaseAction`
  - `plan(mission, history, observation, player_state, turn) -> PlayerPlannerResult`
  - `propose_mission(observation, player_state, inventory, turn) -> MissionGeneratorResult`
  - `reply(sender_name, sender_prompt, message, own_state, own_mission, own_history, turn) -> str`
- Each method wraps its call in `timed_llm_call`, so the four are timed the same way.
- `Player` keeps `think`, `plan`, `_generate_mission_objective` and `receive_message` as the places that set `PlayerState`, apply the result to the mission state, and log; each calls one brain method.
- The brain never receives the world queue, so "replying does no world I/O" holds by construction rather than by a docstring.
- The wrappers stay as the brain's internals in this phase; phase 4 removes them.
- Tests: the thinking is tested on the brain with each chain mocked, asserting both the input it receives and the result returned, no queues (Q9); `Player` tests mock `player.brain`.
- `docs/library/llm.md` and `docs/guides/llm_chains.md` describe the brain as the owner of the four chains.

## Questions

Asked in chat 2026-11-13, answered the same day.

### Q6 arguments or a reference to the player

The brain methods take plain values (proposed), or the brain holds its `Player` and reads the state itself.
Plain values keep the brain testable without a `Player`, and leave the shared mind state to its backlog item.

ANS 2026-11-13: plain values.

### Q7 player name and turn for the timing

`timed_llm_call` needs the player name and the turn. Proposed: the brain gets the name at construction, the turn is passed per call, as `think` does today.
The backlog item on timing in the chain would remove both later.

ANS 2026-11-13: the name at construction, the turn per call.

### Q8 phase 3 and phase 4 together

Phase 4 rewrites the same four brain methods right after phase 3, replacing the wrapper calls with `StructuredLLMChain` and moving the planner and mission input building into the brain.
Keep two phases and two commits (proposed: each diff reads on its own), or one phase.

ANS 2026-11-13: two phases, two commits.

### Q9 tests through scripted chains or mocks

Brain tests through `ScriptedChatConfig` and the real chains (proposed), or with the chains mocked as today.
The scripted model returns fixed values per schema, so a test checks wiring and parsing, not what a prompt receives; the input-passing tests keep a mock.

ANS 2026-11-13: mock the chains, in every brain test.
A mocked chain records what it was called with, so a chain that later starts using an input is already tested the way that checks it; and one pattern for all brain tests.

## Done when

- `Player` builds no chain and calls no chain directly.
- `make check` passes; `make headless` gives the same positions as on `main`.
