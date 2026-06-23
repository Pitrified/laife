# LLM chains

`lAIfe` reasons through a small set of LLM chains, each with one job.
They are built on `llm_core`'s structured chain and prompt loader, so every chain returns a validated pydantic object rather than free text.
The chains live in [the llm package](../library/llm.md) and in a few entity modules.

## The shared pattern

Each chain pairs an input model with a prompt template and an output model.

- The input is a `BaseModelKwargs` whose field names are the variables the prompt must contain.
  The structured chain derives the required variables from these fields, so the prompt and the code cannot drift apart.
- The prompt template is loaded by the `llm_core` prompt loader.
- The output is a pydantic model, so the result is validated on the way out.

This is why the input classes carry a note that their fields define the required prompt variables.
See for example [`world_judge.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_judge.py).

The template text itself lives in [the prompts package](../library/prompts.md), one folder per chain with versioned `vN.jinja` files.
A chain points at its folder by name; the loader resolves the template from there, so prompt wording can change without touching the chain code.

## The chains

- Brain - [`llm/player_brain.py`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/player_brain.py).
  Given the observation and the current mission, returns the next action.
  This is the core decision step of a turn.
- Planner - [`llm/player_planner.py`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/player_planner.py).
  Decomposes a hard mission into ordered sub-missions, using the mission history as context.
  Triggered by the plan action.
- Replier - [`llm/player_replier.py`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/player_replier.py).
  Produces an in-character reply to a message from another player.
  It is called from inside the world's interaction routing, so it stays free of world I/O.
- Mission generator - [`llm/mission_generator.py`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/mission_generator.py).
  Proposes a new mission objective from the current world observation, so a player without a goal can find one.
- World judge - [`entities/world_judge.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_judge.py).
  Decides whether a build or craft action is valid and returns a success flag with feedback.
  This is the world's reasoning, not the player's.

## Missions as data

The mission and its history are plain models in [`llm/mission.py`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/mission.py).
Missions carry an objective, a status, and a list of action and result entries, and they can nest.
They render to prompt text so the brain and planner always see the full context they have accumulated.

## Configuration

Which model each chain uses, and with what settings, comes from the LLM service params.
See [params and config](params_config.md) for how chat, embedding, and search settings are assembled per environment.
