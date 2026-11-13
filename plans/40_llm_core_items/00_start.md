---
status: done
priority: 0
description: |
  Four items that end in llm-core or in laife's use of it: a `reasoning_effort` field on `ChatOpenAIConfig`, timing every LLM call in the chain, the scripted chat model moved to llm-core, and the duplicated `Singleton`.
---

# llm-core items - bootstrap

Picked 2026-11-13 by the user, in this order: `reasoning_effort`, "Timing every LLM call", "Scripted chat model to llm-core", "Singleton reset".
The first is an llm-core follow-up from folder 38; the other three are `plan.md` items under "Code health".

## What the code shows

### `reasoning_effort`

- llm-core's `ChatOpenAIConfig` has `model`, `model_provider`, `api_key`, and `temperature` from `ChatConfig`; no `reasoning_effort`.
  `create_chat_model` passes `to_kw(exclude_none=True)` to `init_chat_model`, so a value can already go in through `kwargs={"reasoning_effort": ...}`; checked in folder 38.
- langchain-openai's `ChatOpenAI.reasoning_effort` is `str | None = None`.
  It drops a non-default temperature on `gpt-5*` models unless `reasoning_effort` is `"none"`.
- laife's `ChatParams.load_params` builds `ChatOpenAIConfig(temperature=1, model="gpt-6-luna")`, with a comment that luna only accepts temperature 1 unless reasoning is off and that the config has no field for it.
  fala-language-tutor's prompt lab found that gpt-6-luna and gpt-5.4-nano accept temperature 0.7 with `reasoning_effort: none` (its folder 14).

### Timing

- `timed_llm_call(player, turn, model, stage)` in `laife.meta.logger` emits one `llm_call` record when the wrapped call returns; none if it raises.
- `PlayerBrain._timed` wraps its four chain calls; the brain takes the player name at construction and the turn per call for this alone.
- `WorldJudge`'s three calls are not timed.
- The JSON sink in `configure_logging` takes every loguru record, unfiltered; llm-core logs with loguru too.
- laife uses no `contextualize` or contextvars today.
- Trap for context-based timing: `Player.receive_message` runs inside the world's task (`WorldRunner.route_interaction`), so a player and turn set in the replier's own task are not visible there.
  The judges also run in the world's task, for a request that carries `player_name` and `turn`.

### Scripted chat

- `laife.llm.scripted_chat`: `ScriptedChatModel(script)` answers `with_structured_output(schema)` with a `RunnableLambda` that ignores the prompt; `answer(schema)` is an `if` chain over laife's output models, `ActionEnvelope` taking the next scripted action, cycling.
  Errors: `UnscriptedSchemaError`, `EmptyScriptError`, `UnscriptedCallError`. Also `default_script(other_player)` and `ScriptedChatConfig(script, model="scripted")`.
- llm-core's `testing/fake_chat_model.py`: `FakeChatModel(responses)` cycles a list of messages regardless of schema and parses JSON into the schema; `FakeChatModelConfig`.
- The general part is a model that answers by schema from a mapping; the mapping, the script and its cycling are laife's.
- Each chain builds its own model from the config, so the action cycle lives in the action chain's model.
  If the answers become callables held by the config, the cycle state must still be per model, not shared through the config.

### Singleton

- `src/laife/meta/singleton.py` is identical to llm-core's `llm_core/metaclasses/singleton.py`. `LaifeParams` and `Alog` use laife's copy.
- No reset hook in either; no test reaches into `_instances` (checked 2026-11-12 and again now).

## Proposed shape

- One folder, one phase per item, in the user's order.
- The llm-core changes go on one llm-core branch; laife develops against them with `make dev-llm-core`, and one llm-core release at the end, v0.4.0 since it adds API; laife then pins the tag (Q1).
- Phase 1, `reasoning_effort`: an optional `reasoning_effort: str | None = None` on `ChatOpenAIConfig`, matching langchain-openai's type; a test that it reaches the built model. laife's settings per Q2.
- Phase 2, timing in the chain, per Q3.
- Phase 3, scripted chat: llm-core gets a model and config answering by schema from a mapping, with the unscripted-schema and free-text errors; laife keeps the mapping, the script, `EmptyScriptError` and `default_script` (Q4).
- Phase 4, Singleton: laife deletes its copy and imports llm-core's; the reset hook per Q5.
- Evidence per phase: `make check`, and `make headless` ends at the same positions with the same `llm_call` records, plus the judges' new ones after phase 2.

## Questions

### Q1 folders and releases

Proposed: one folder, four phases; llm-core work on one branch with one v0.4.0 release at the end; laife runs on the editable llm-core until then and pins the tag in the last commit.
The `plan.md` note says the scripted chat gets a folder of its own; here it is a phase of its own instead, with its own commit in each repo.
Alternative: a release per item, four tags to push.

ANS 2026-11-13: ok.

### Q2 what laife sets for `reasoning_effort`

The field alone changes no run.
Setting it in `ChatParams` changes every live call, and only a paid run shows the effect.
Options: (a) the field only, laife keeps `temperature=1` and no effort, the comment updated; (b) `reasoning_effort="none"` with a lower temperature, as fala uses, verified by a short capped live run you approve.
Proposed: (a) in this folder, (b) as a backlog item with its own run.

ANS 2026-11-13: either; laife's chat params were never tuned, which is future work. Taken as (a), with a backlog item for the tuning.

### Q3 where timing lives

(A) In llm-core: `StructuredLLMChain` gets an optional `name` and an optional callback called with name, model and elapsed seconds after a successful `ainvoke`/`invoke`.
laife passes one callback that writes the `llm_call` record; player and turn come from `slog.contextualize`, set per turn in `Player.play` and by the runner around a judge call and around `route_interaction` (with the replier's name and turn).
The brain loses `player_name`, the `turn` arguments and `_timed`; every chain built with the callback is timed, including the judges and any new chain.
(B) In laife only: `WorldJudge` gets a `_timed` like the brain, taking player and turn from the request.
Smaller, no llm-core change, but each new chain site has to remember it, which is the gap the backlog item names.
Proposed: (A). The context setting in the world's task is the part to get right; the headless log shows it, since a reply record must keep the replier's name.

ANS 2026-11-13: (A).

### Q4 shape of the scripted model in llm-core

Proposed: `ScriptedChatModel(answers: dict[type[BaseModel], Callable[[], BaseModel]])` and `ScriptedChatConfig` with a `build_answers()` hook a subclass overrides, called once per `create_chat_model`, so each model gets fresh answer callables and the action cycle stays per model.
Name: `llm_core.testing.scripted_chat_model`, beside `fake_chat_model`.
`model` defaults to `"scripted"`, which laife's `llm_call` records show.

ANS 2026-11-13: ok.

### Q5 Singleton reset

Proposed: no reset hook; the backlog item is closed with the duplicate removed, since still nothing needs a reset.

ANS 2026-11-13: ok; at most it stays an open point in python-project-template, which is not touched by this folder.

## Done when

- llm-core v0.4.0 holds the field, the chain timing (if Q3 A) and the scripted model; laife pins it.
- laife has no copy of `Singleton` or of the general scripted model; every LLM call writes an `llm_call` record.
- `make check` passes in both repos; `make headless` gives the same positions as on `main`.
