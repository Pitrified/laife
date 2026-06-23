# llm

The LLM reasoning a player uses, and the mission model it reasons about.
Source: [`src/laife/llm/`](https://github.com/Pitrified/laife/tree/main/src/laife/llm).
For the shared chain pattern and how the chains fit a turn see [the LLM chains guide](../guides/llm_chains.md).

## Chains

- [`player_brain.py`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/player_brain.py) - the brain.
  Turns an observation and the current mission into the next action.
- [`player_planner.py`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/player_planner.py) - the planner.
  Decomposes a mission into ordered sub-missions.
- [`player_replier.py`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/player_replier.py) - the replier.
  Generates an in-character reply to a message from another player, without touching world I/O.
- [`mission_generator.py`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/mission_generator.py) - the mission generator.
  Proposes a fresh mission objective from the current world observation.

Each chain pairs a `BaseModelKwargs` input, whose fields define the required prompt variables, with a prompt template and a validated pydantic output.

## Mission model

[`mission.py`](https://github.com/Pitrified/laife/blob/main/src/laife/llm/mission.py) defines the mission and its history.
A mission carries an objective, a status, and a list of action and result entries, and missions can nest.
The history renders to prompt text, so the brain and planner always see what has been tried.

The world judge that validates build and craft actions is the world's reasoning rather than the player's; it lives in [the entities package](entities.md).
