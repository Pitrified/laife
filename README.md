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
poetry run python game/main.py
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
Missions can be nested.

If a tool is needed to solve a mission, the player has to find the tool first.
If the tool does not exist, the player has to create it.

New building blocks can be created by the players.

World entities:
* Player
* Building
* Tool
* Terrain

Game logic is dynamic:
given a mission, the player decides which tool to use, and where to go to use it.
The engine checks that the player has the tool,
the LLM checks that the tool can be used in the location to solve the mission.

A swap in control might happen:
the player can send requests to the world to do some action,
and the world answers with the result.
The world never tells the player what to do.

In `to_prompt` there could be a position parameter,
so that in the prompt the location is dynamically converted to text eg "to the south".

A player in the beginning does not know the world.
One of the option is observe.

### Features

- [x] : World with renderer
- [ ] : Map of the world with entities:
    - [ ] : Different terrain
    - [ ] : Different objects
- [ ] : Translate the map into a prompt
- [ ] : Assign a mission to a player based on the map
    - [ ] : If a mission is too complex, break it down into sub-missions
    - [ ] : Share the mission with the world: the player can ask for help
- [ ] : Create a tool to solve the mission
    - [ ] : If the tool does not exist, create it
    - [ ] : Create an image of the tool
- [ ] : Solve the mission
- [ ] : The mission could be building a building


### Startup Entities

- terrain:
    - forest
    - lake    
    - fertile land
- building:
    - house - to rest
    - factory - to create tools
    - farm - to grow food
- tools:
    - bucket
    - axe
    - hammer
    - hoe
