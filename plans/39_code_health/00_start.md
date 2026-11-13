---
status: done
priority: 0
description: |
  Code health items picked from the `plan.md` backlog: the duplicated `BaseModelKwargs`, the world request boilerplate, the unused providers and the install weight, the player's thinking moved into `PlayerBrain`, and the chain wrappers around llm-core's `StructuredLLMChain`.
---

# code health - bootstrap

Picked 2026-11-13 from the `plan.md` section "Code health", five of its eight items.
The items come from the outside read in folder 33, checked against the code during folder 36.

## Selection

Taken with the user, 2026-11-13.

- In: "Duplicated `BaseModelKwargs`", "World request boilerplate", "Provider layering", "Install weight", "One base for the LLM chain wrappers".
- Out, folded: "One logging call per event" moves under the backlog item "Renderer: pygame or a web app", beside the terminal and log trim; it depends on what the logs become.
- Out, own folder later: "Scripted chat model to llm-core". It needs an llm-core release and is not mixed with other work.
- Out, kept with its scope corrected: "Singleton reset". The original finding said tests reach into `Singleton._instances`; on 2026-11-12 no test did. The missing reset hook is true, and nothing needs it yet.

## What the code shows

### `BaseModelKwargs`

`src/laife/data_models/basemodel_kwargs.py` is already a re-export of llm-core's class, not a copy.
The five chain input models import it from there.

### World requests

`WReq` and the six `WRec*` classes in `src/laife/entities/world_channel.py` are plain classes.
Each `WRec*` takes its own fields and forwards `*args, **kwargs` to `WReq.__init__`, with two `noqa` lines, and writes its own `__str__`.
`WReq.__init__` also sets `player_name` and `turn`, stamped later by `Player._world_request`.

### Chain wrappers

llm-core's `StructuredLLMChain(chat_config, prompt_str, input_model, output_model)` validates the prompt variables against the input model and has `invoke` and `ainvoke`.
laife wraps it five times, not all the same way:

- `ActionPicker` (`entities/action.py`) takes `chat_config` and `prompt_str`, and unwraps `ActionEnvelope.act`.
- `WorldActionJudge` (`entities/world_judge.py`) takes `chat_config` and `prompt_str`; `WorldRunner` loads the three judge prompts and builds three judges.
- `MissionGenerator` and `PlayerPlanner` (`llm/`) take a `*Config(chat_config, prompt_loader_config)`, load their prompt in `__post_init__`, and build their input from domain objects inside `ainvoke`.
- `PlayerReplier` (`llm/`) takes the same kind of config; its input is built in `Player.receive_message`.

Each input model repeats the same docstring paragraph about the validation.

### `Player` and `PlayerBrain`

`entities/player.py` is one class with six concerns:
the body (name, size, position, state, `move_delta`, `render_state`),
the turn loop (`play`, `turn`, `sim_control`),
world I/O (the queues, `_world_request`, the action handlers),
the mind state (`mission`, `history`, `last_observation`, `inventory`, `_update_mission_from_response`, `_start_new_mission`),
the thinking (four chains built in `__init__`, `think`, `_generate_mission_objective`, the LLM half of `plan`, `receive_message`),
and logging spread through all of them.

`PlayerBrain` (`llm/player_brain.py`) was meant as the thinking layer, separate from the player.
Today it holds only the action chain and adds three things over `ActionPicker`: loading the action prompt, building `ActionPickerInput` from the domain objects' `to_prompt()`, and the `timed_llm_call` around the call.
It holds no state.
The other three player chains went straight into `Player`, each with its own `timed_llm_call` at the call site.
Tests reach through it: `tests/llm/test_player_brain.py` replaces `brain.action_picker`, and `tests/entities/test_world_request_errors.py` mocks `brain.think`.
The world judges have no `timed_llm_call` at all.

`WorldRunner` calls the replier through `Player.receive_message`, which must stay free of world I/O.

### Prompt loading

`WorldRunner.__init__` builds a `PromptLoaderConfig(base_prompt_fol=..., prompt_name=...)` and loads it three times; `Player.__init__` builds the same config four times and the wrappers load it.

### Providers

`ChatParams` builds OpenAI, Azure, HuggingFace and Ollama configs; `EmbeddingsParams` builds OpenAI, Azure, HuggingFace and Ollama.
Every caller takes `.default`, the OpenAI one.
Outside `params/`, nothing uses the embeddings or the vector store yet; they are kept for the backlog item on utensils and the vector store.
Five test files build an `OllamaChatConfig` as a placeholder config: `tests/llm/test_mission_generator.py`, `test_player_planner.py`, `test_structured_chain.py`, `test_player_brain.py`, `tests/entities/test_world_judge.py`.

### Install weight and `laife.embed`

`.venv` is several GB.
`pyproject.toml` depends on `llm-core[all]`, whose `whisper` extra pulls torch, and whose `huggingface` extra pulls sentence-transformers; laife also depends on `transformers` directly.

`src/laife/embed/` is a copy of langchain-huggingface's `SentenceTransformersEmbeddings` plus a `pydantic.v1` helper, not a wrapper of llm-core.
Nothing in `src`, `tests` or `game` imports it.
Its only user, `scratch_space/embed_/sample.ipynb`, already imports modules that no longer exist (`laife.config`, `laife.llm.vector_db`).

Whether anything else still pulls torch after narrowing is unknown until `uv tree` is read on the narrowed lock.

## Order

Taken with the user: A, then C, then the chain work, so the chain diff is read against the slimmer params.
The brain move goes before the wrapper removal (proposed by the agent, 2026-11-13): the brain is where the chains end up, so removing the wrappers first would build them in `Player` only to move them again.

## Questions

### Q1 chain wrappers

ANS 2026-11-13: use `StructuredLLMChain` directly; assess what `PlayerBrain` adds (above).

### Q2 providers

ANS 2026-11-13: OpenAI only; embeddings are on OpenAI already.

### Q3 `PlayerBrain`

Proposed first: fold it into `Player.think()`.
Reopened by the user: the brain was meant as the thinking layer and should grow instead.

ANS 2026-11-13: grow the brain, in a dedicated phase.
It owns the four player chains, with methods such as `next_action`, `plan`, `propose_mission`, `reply`; `Player` keeps the body, the turn loop and world I/O.
The thinking can then be tested without queues.
The mind state does not move now. It goes to the backlog: one player instance has one brain instance, tightly tied, so a shared mind state between the two can exist; to be assessed and planned on its own.

### Q4 `laife.embed`

ANS 2026-11-13: remove the dead code, `src/laife/embed/` and the notebook. Keep the embeddings and vector store params, which are planned for use.

### Q5 where prompt loading lives

Proposed: a `load_prompt(name) -> str` helper, since every config holds only a name.

ANS 2026-11-13: no helper; keep `PromptLoaderConfig`.
A config object gives the call its structure even while it has one field; a helper taking the fields as arguments grows a parameter for each new field, such as a prompt version.
The rule is recorded in `.github/copilot-instructions.md`, "How to build".
