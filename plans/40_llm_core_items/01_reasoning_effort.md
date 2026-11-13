---
status: planned
---

# Phase 1 - `reasoning_effort` on `ChatOpenAIConfig`

## Overview

A typed field for what laife and fala pass today through `kwargs`. Context: [`00_start.md`](00_start.md), Q2.

## Steps

llm-core, on a new branch `feat/v0_4_items` from `main` (all three llm-core phases go on it):

- `ChatOpenAIConfig.reasoning_effort: str | None = None`, typed as langchain-openai's; the docstring says it is left out of the request when `None` and that langchain drops a non-default temperature on `gpt-5*` unless it is `"none"`.
- Test in `tests/chat/`: the field reaches the built `ChatOpenAI` (`create_chat_model().reasoning_effort`), and `None` is not passed to `init_chat_model`.
- CHANGELOG under an `Unreleased` heading.

laife:

- `ChatParams.load_params`: the comment no longer says the config lacks the field; settings unchanged (temperature 1, gpt-6-luna, no effort).
- `plan.md`: a backlog item "Tuning the chat params": model, temperature and `reasoning_effort` were never tuned for laife, and a change needs a capped live run.

## Done when

- `make check` passes in llm-core (on its own venv) and in laife on `make dev-llm-core`.
- `make headless` unchanged: same positions, same `llm_call` records.
