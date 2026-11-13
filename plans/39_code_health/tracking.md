# code health - implementation tracking

Five backlog items from "Code health": `BaseModelKwargs`, world request boilerplate, unused providers, install weight, chain wrappers; the chain work grew a phase that moves the player's thinking into `PlayerBrain`.
Analysis and questions in [`00_start.md`](00_start.md).

## Key decisions

- Items 3 (logging), 5 (scripted chat to llm-core) and 6 (singleton reset) stay out; see `00_start.md`, "Selection".
- Chains use llm-core's `StructuredLLMChain` directly (Q1).
- OpenAI only, chat and embeddings; embeddings and vector store params stay (Q2, Q4).
- `PlayerBrain` owns the four player chains; the mind state stays on `Player` and goes to the backlog (Q3).
- `laife.embed` and its notebook are deleted (Q4).
- Prompt loading keeps `PromptLoaderConfig`, no helper (Q5).
- Order A, C, brain, wrappers.
- Requests are `@dataclass(kw_only=True, eq=False)` (phase 1).
- Tests use `ScriptedChatConfig` as the placeholder; `default` keeps its name (phase 2).
- `langgraph` and `pysqlite3-binary` go, the latter if chroma passes a check; `ipywidgets` stays (phase 2).

## Phases

| #  | Phase                       | Plan                                           | Status |
| -- | --------------------------- | ---------------------------------------------- | ------ |
| 1  | A: mechanical               | [`01_mechanical.md`](01_mechanical.md)         | planned |
| 2  | C: OpenAI only and install  | [`02_openai_only.md`](02_openai_only.md)       | planned |
| 3  | B1: thinking into the brain | [`03_player_brain.md`](03_player_brain.md)     | draft  |
| 4  | B2: chain wrappers          | [`04_chain_wrappers.md`](04_chain_wrappers.md) | draft  |

Status values: draft / planned / in progress / done / superseded / discarded.

## Log

Append-only. Newest at the bottom.

- 2026-11-13 : picked five items from `plan.md` with the user; read the wrappers, `PlayerBrain`, the world requests, the provider params and the install; Q1, Q2 and the order answered; Q3-Q5 open.
- 2026-11-13 : assessed `Player`, `PlayerBrain`, `laife.embed` and the prompt loading; Q3-Q5 answered; the brain move split out as phase 3, the wrappers moved to phase 4; mind state and chain timing added to `plan.md`.
- 2026-11-13 : consistency review of phases 1 and 2 against the code: docs pages and nav, `eq=False`, the test placeholder config, `dev-llm-core` extras, `nokeys.env`; unused dependencies decided with the user; phases 1 and 2 set to `planned`.
