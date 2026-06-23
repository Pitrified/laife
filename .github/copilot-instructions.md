# lAIfe - Copilot Instructions

## Project overview

lAIfe is an LLM-driven life-simulation game built on Pygame + asyncio. Players are autonomous AI agents that perceive the world, plan missions, and issue actions; the game engine validates and executes those actions. Python 3.13, managed with **uv**.

## Running & tooling

```bash
uv run game/main.py          # run the game
uv run pytest                # run tests
uv run ruff check .          # lint (ruff, ALL rules enabled - see ruff.toml)
uv run pyright               # type-check (src/ and tests/ only)
```

A `Makefile` wraps these common commands; prefer the targets directly when one fits the task (`make help` lists them):

```bash
make sync       # install all dependencies (extras and groups)
make run        # run the game
make test       # run tests
make lint       # lint with ruff
make format     # format with ruff
make typecheck  # type-check with pyright
make docs       # serve the docs locally with MkDocs
```

Credentials live at `~/cred/laife/.env` (loaded by `load_env()` in `src/laife/params/load_env.py`). See `nokeys.env` for required keys (`OPENAI_API_KEY`, `AZURE_OPENAI_*`).

## Architecture layers

| Layer         | Path                                    | Role                                                                                                                                              |
| ------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Game entry    | `game/main.py`                          | Pygame loop + asyncio bridge; spawns `WorldRunner.simulate()` and `Player.play()` as concurrent tasks, then drives the Pygame event loop          |
| Rendering     | `src/laife/rendering/world_renderer.py` | `WorldRenderer` reads `WorldRunner` state and converts it into Pygame sprites/window; display dependency is isolated here, `WorldRunner` has none |
| Simulation    | `src/laife/entities/world_runner.py`    | Authoritative state, processes `WReq` messages                                                                                                    |
| Entities      | `src/laife/entities/`                   | `Player`, `Building`, `Utensil`, `Terrain`                                                                                                        |
| AI brain      | `src/laife/llm/player_brain.py`         | `PlayerBrain.think()` → `BaseAction`                                                                                                              |
| Actions       | `src/laife/entities/action.py`          | Discriminated union: `ActionMove , ActionBuild , ActionCraft , ActionPlan`                                                                        |
| Missions      | `src/laife/llm/mission.py`              | `Mission` owns `MissionHistory`; supports nested sub-missions                                                                                     |
| LLM services  | `src/laife/llm_services/`               | Provider-agnostic wrappers (Ollama, OpenAI, Azure OpenAI, HuggingFace)                                                                            |
| Config/params | `src/laife/params/`                     | Singleton `LaifeParams`; `LaifePaths` for all filesystem refs                                                                                     |

## Key patterns

**World <-> Player communication via async queues**  
Players put `WReq` subclasses (e.g., `WRecBuild`, `WRecObserve`) into `WorldRunner.input_queue`. Each request carries its own `response_queue`; the runner puts a `WRes` back there. This decouples the simulation loop from any display dependency.

**LLM provider abstraction via config subclasses**  
All LLM services use the same pattern: a `BaseModelKwargs` config subclass with a factory method that calls the underlying LangChain constructor via `to_kw(exclude_none=True)`. Never instantiate these objects directly.

- Chat: `ChatConfig.create_chat_model()` -> `init_chat_model`; subclasses in `src/laife/llm_services/chat/config/` (Ollama, OpenAI, AzureOpenAI, HuggingFace)
- Embeddings: `EmbeddingsConfig.create_embeddings()` -> `init_embeddings`; subclasses in `src/laife/llm_services/embeddings/config/`
- Vector store: `VectorStoreConfig` (abstract); `ChromaConfig` in `src/laife/llm_services/vectorstores/config/`

**Versioned Jinja prompts**  
Prompts live in `src/laife/prompts/<name>/vN.jinja`. Use `PromptLoader` with `version="auto"` to pick the highest version. Add a new prompt version by creating `vN+1.jinja`; never edit an existing version file.

**`Vectorable` protocol for entity serialization**  
Entities that round-trip through a vector store must implement `to_document() → Document` and `from_document(doc) → Self`, writing `entity_type` into `doc.metadata`. See `src/laife/entities/vectorable.py`.

**`BaseModelKwargs`**  
Config classes extend `BaseModelKwargs` (not plain `BaseModel`) when their fields need to be forwarded as `**kwargs` to a third-party constructor. `to_kw(exclude_none=True)` flattens a nested `kwargs` dict at the top level.

**`LaifeParams` singleton**  
Access project-wide config and paths via `get_laife_params()` from `src/laife/params/laife_params.py`. Environment is controlled by `ENV_STAGE_TYPE` (`dev`/`prod`) and `ENV_LOCATION_TYPE` (`local`/`render`) env vars.

## `to_prompt()` convention

Every entity and domain object that feeds into an LLM context exposes a `to_prompt() -> str` method. Build prompts by composing these, not by manually constructing strings.

## Style rules

- Never use em dashes (`--` or `---` or Unicode `—`). Use a hyphen `-` or rewrite the sentence.

## Testing & scratch space

- Tests live in `tests/` (mirrors `src/laife/` structure).
- `scratch_space/` holds numbered exploratory notebooks and scripts (e.g., `12_action_structure/`, `17_configurable_vectorstore/`). These are not part of the package; ruff ignores `ERA001`/`F401`/`T20` there.

## Linting notes

- `ruff.toml` targets Python 3.13 with `select = ["ALL"]`. Key ignores: `D203`, `D213` (docstring style), `FIX002`/`TD002`/`TD003` (TODO formatting).
- Tests additionally allow `S101` (assert), `SLF001` (private access), `PLR2004` (magic values).

## End-of-task verification

After every code change, run the full verification suite before considering the task done:

```bash
uv run pytest && uv run ruff check . && uv run pyright
```
