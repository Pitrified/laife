# llm-core items - implementation tracking

`reasoning_effort`, timing in the chain, scripted chat to llm-core, `Singleton`.
Analysis and questions in [`00_start.md`](00_start.md).

## Key decisions

- One folder, one llm-core branch, one v0.4.0 release at the end; laife runs on `make dev-llm-core` until the pin (Q1).
- `reasoning_effort` is added as a field only; tuning laife's chat params goes to the backlog (Q2).
- Timing in `StructuredLLMChain` through a `name` and an `on_call` callback; player and turn from `slog.contextualize` (Q3).
- `ScriptedChatModel` and its config with `build_answers()` in `llm_core.testing`; laife keeps the script and answers (Q4).
- laife's `Singleton` copy goes; no reset hook (Q5).

## Phases

| # | Phase                    | Plan                                             | Status |
| - | ------------------------ | ------------------------------------------------ | ------ |
| 1 | reasoning_effort         | [`01_reasoning_effort.md`](01_reasoning_effort.md) | planned |
| 2 | timing in the chain      | [`02_timing.md`](02_timing.md)                   | planned |
| 3 | scripted chat            | [`03_scripted_chat.md`](03_scripted_chat.md)     | planned |
| 4 | Singleton, release, pin  | [`04_singleton.md`](04_singleton.md)             | planned |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-11-13 : picked four items with the user; read `ChatOpenAIConfig`, `StructuredLLMChain`, `timed_llm_call`, the scripted and fake chat models and both `Singleton`s; Q1-Q5 open.
- 2026-11-13 : Q1-Q5 answered; phase files written; checked loguru's merge of context and bound extra.
- 2026-11-13 : user said commit and implement; phases set to planned.
