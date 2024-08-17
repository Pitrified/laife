# lAIfe

Let's make AI rule the world!

## Setup

### Install package

```bash
poetry install
```

### Openai key

place the openai key in `src/laife/config/credentials.py`:

```python
from pydantic.v1 import SecretStr

OPENAI_API_KEY = SecretStr("your-openai-api-key")
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

New building blocks can be created by the players.

World entities:
* Player
* Building
* Tool
* Terrain

Missions can be nested.

### Features

1. World with renderer
1. Map of the world with entities:
    1. Different terrain
    1. Different objects
1. Translate the map into a prompt
1. Assign a mission to a player based on the map
    1. If a mission is too complex, break it down into sub-missions
    1. Share the mission with the world: the player can ask for help
1. Create a tool to solve the mission
    1. If the tool does not exist, create it
    1. Create an image of the tool
1. Solve the mission
1. The mission could be building a building
