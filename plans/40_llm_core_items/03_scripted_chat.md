---
status: planned
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
