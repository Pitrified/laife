---
status: done
---

# Phase 3 - scripted chat model to llm-core

## Overview

The model that answers by output schema moves to llm-core; laife keeps what it answers. Context: [`00_start.md`](00_start.md), Q4.

## Steps

llm-core, `llm_core/testing/scripted_chat_model.py`:

- `UnscriptedSchemaError(schema)` and `UnscriptedCallError`, messages as in laife today.
- `ScriptedChatModel(answers: dict[type[BaseModel], Callable[[], BaseModel]])`: `with_structured_output(schema)` returns a `RunnableLambda` that ignores the prompt and calls `answers[schema]()`, raising `UnscriptedSchemaError` for a missing schema; `_generate` raises `UnscriptedCallError`; `_llm_type` is `scripted`.
- `ScriptedChatConfig(model="scripted", model_provider="scripted")` with `build_answers()` returning `{}`; `create_chat_model()` calls it once per model.
- Tests in `tests/testing/`: answers by schema, a fresh `build_answers` per model, both errors.

laife, `laife.llm.scripted_chat`:

- `ScriptedChatConfig` subclasses llm-core's, keeps `script`, and overrides `build_answers`: an action cycle over the script, created per call so each model has its own, plus the fixed judge, mission, planner and reply answers.
- `EmptyScriptError` and `default_script` stay; `ScriptedChatModel`, `UnscriptedSchemaError`, `UnscriptedCallError` go, and the tests import the errors from llm-core.
- Docs: `docs/guides/headless.md`, the `.github/copilot-instructions.md` line on `UnscriptedSchemaError`; `plan.md` item removed.

## Done when

- `make check` passes in both repos.
- `make headless` gives the same positions and the same record sequence per player as after phase 2.

## Decided by the agent while implementing

For the user's review, 2026-11-13.

- `Answers` is a type alias in llm-core's module, exported for subclasses' `build_answers` signatures; `ScriptedChatModel` and `ScriptedChatConfig` are also exported from `llm_core.testing`.
- laife imports llm-core's config as `BaseScriptedChatConfig` and keeps the name `ScriptedChatConfig` for its subclass, so callers and docs keep their import.
- The action cycle is an `itertools.cycle` over the script, built in `build_answers`; an empty script raises `EmptyScriptError` when an action is asked, as before.
- A laife test checks that two models from one config each start at the top of the script.

## Outcome

- llm-core 7f11dd3: `llm_core.testing.scripted_chat_model` with the model, config, `Answers` and both errors; six tests; CHANGELOG.
- laife: `laife.llm.scripted_chat` holds `EmptyScriptError`, `default_script` and `ScriptedChatConfig` on llm-core's base; the model and the two errors are gone.
- Tests: 272. One test added (a cycle per model); `tests/test_models_build.py` lost its case for laife's `ScriptedChatModel`, found by diffing the collected test ids against the last commit.
- `make check` passes. `make headless` ends at the same positions; per player, the record sequence matches phase 2's run, judges included.
- Docs: `docs/guides/headless.md` and the instructions line on `UnscriptedSchemaError`; `plan.md` item removed.
