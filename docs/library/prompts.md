# prompts

The Jinja prompt templates that drive the LLM chains.
Source: [`src/laife/prompts/`](https://github.com/Pitrified/laife/tree/main/src/laife/prompts).
This package holds template files only, no Python; the chains that use them live in [the llm package](llm.md) and [the entities package](entities.md).

## Layout

Templates are grouped by the chain that uses them, one folder per chain, with one file per version:

- [`player_brain/`](https://github.com/Pitrified/laife/tree/main/src/laife/prompts/player_brain) - the brain, with `v1.jinja` and `v2.jinja`.
- [`player_planner/`](https://github.com/Pitrified/laife/tree/main/src/laife/prompts/player_planner) - the planner.
- [`player_reply/`](https://github.com/Pitrified/laife/tree/main/src/laife/prompts/player_reply) - the replier.
- [`mission_generator/`](https://github.com/Pitrified/laife/tree/main/src/laife/prompts/mission_generator) - the mission generator.
- [`world_judge_build/`](https://github.com/Pitrified/laife/tree/main/src/laife/prompts/world_judge_build), [`world_judge_craft/`](https://github.com/Pitrified/laife/tree/main/src/laife/prompts/world_judge_craft), [`world_judge_complete/`](https://github.com/Pitrified/laife/tree/main/src/laife/prompts/world_judge_complete) - the world judge, one folder per action it validates.

## How a template is selected

A chain is configured with a `PromptLoaderConfig` that names the base folder and the chain:
the base folder is `prompts_fol` from [the paths](params.md), which resolves to this package, and the prompt name is the chain folder, such as `player_brain`.
The loader reads the templates from that folder; keeping versions side by side as `v1.jinja`, `v2.jinja` lets a prompt evolve without deleting the previous wording.
See the construction sites in [`entities/player.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/player.py) and [`entities/world_runner.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_runner.py).

## Template variables

Each template fills the variables the chain provides, for example `mission`, `history`, `observation`, `player_state`, and `inventory` for the brain.
Those variable names are not free-form: they are the fields of the chain's input model, and the structured chain derives the required set from those fields, so a template that references an unknown variable is caught.
See [the LLM chains guide](../guides/llm_chains.md) for that input-model-to-prompt contract.
