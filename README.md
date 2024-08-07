# lAIfe

Let's make AI rule the world!

## Setup

### Install package

```bash
poetry install
```

### Run the game

```bash
poetry run python scratch_space/game/agent_loop.py
```

## Ideas

There are players, that do things in the environment.

Players have states.

There are objects in the environment.

The players can interact with the objects, and with each other.

A player has a mission.
If a player has nothing to do, it can interact with the environment to find a mission.
To complete the mission, the player has to interact with the environment.

A mission can be solved in several steps.

If a tool is needed to solve a mission, the player has to find the tool first.
If the tool does not exist, the player has to create it.
