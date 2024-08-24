# lAIfe

Let's make AI rule the world!

## Setup

### Install package

```bash
poetry install
```

edit the chromadb package to deal with the old sqlite3 version

`~/.cache/pypoetry/virtualenvs/laife-IdkopDz3-py3.11/lib/python3.11/site-packages/chromadb/__init__.py`

around line 86 where the import fails

```
            __import__("pysqlite3")
            import sys
            sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
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
    - A terrain is an entire section of map
    - Default background is grass
    - When building the prompt, the area of each type of terrain is calculated
      and described

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

A mission has an objective, a history of actions, and a status (done, failed, in progress).
There can be sub-missions, and the nesting level is tracked.

The chosen action is validated by the world, it must exist as an option, and be possible in the current state of the world.
The world can answer with a feedback, which is placed in the history of the mission.
The player LLM iterates on the mission with more history, and can pick a different action.
One of the player LLM response option is to split the mission into sub-missions.

The validation of whether an action actually solves the mission is done by the world LLM.

### Features

- [x] : World with renderer
    - [ ] : Prettier background with tiled grass
    - [ ] : Prettier terrain with tiled terrain types
    - [ ] : Prettier buildings with a big building in the center and a tiled garden
    - [ ] : Tools can be held by the player
- [x] : Swap player and world queue control,
        the player sends requests to the world to do some action,
        and the world answers with the result
    - [x] : Formalize the player and world interaction
    - [ ] : Make the list of possible player actions
- [ ] : Map of the world with entities:
    - [x] : Different buildings
    - [ ] : Different terrain
    - [ ] : Make the map dynamic with dataclasses
            or some kind of loader
- [ ] : Vector db of the world entities
    - [ ] : Different tools
- [ ] : Translate the map into a prompt
- [ ] : Convert the `to_prompts` into langchain objects
- [ ] : Assign a mission to a player based on the map
    - [ ] : If a mission is too complex, break it down into sub-missions
    - [ ] : Share the mission with the world: the player can ask for help
- [ ] : Create a tool to solve the mission
    - [ ] : If the tool does not exist, create it
    - [ ] : Create an image of the tool
- [ ] : Solve the mission
- [ ] : The mission could be building a building
- [ ] : Add an alive parameter to the player,
        if the player is not alive, kill the async task
        by exiting the loop
- [ ] : Add a player inventory


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
