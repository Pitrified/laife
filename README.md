# lAIfe

Let's make AI rule the world!

## Setup

### Pygame

might need SDL to solve

`RuntimeError: Unable to run "sdl-config". Please make sure a development version of SDL is installed.`

which actually need SDL2

```
sudo apt install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    libjpeg-dev \
    libpng-dev 
```


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

If an utensil is needed to solve a mission, the player has to find the utensil first.
If the utensil does not exist, the player has to create it.

New building blocks can be created by the players.

World entities:
* Player
* Building
* Utensil
* Terrain
    - A terrain is an entire section of map
    - Default background is grass
    - When building the prompt, the area of each type of terrain is calculated
      and described

Game logic is dynamic:
given a mission, the player decides which utensil to use, and where to go to use it.
The engine checks that the player has the utensil,
the LLM checks that the utensil can be used in the location to solve the mission.

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

The `Brain` thinks about a `Mission` and generates an `Action`.
All the action except `move` are done as world requests.
The response of the world is set into the mission history.

Add a langchain `tool` to compute distance between two points on the map.

There are mission and actions.

Add decorators to player functions to update the state of the player.

The `Mission` do not need a `MissionType`, it has to be inferred from the mission description.
This is because missions can be very dynamic and complex, world/brain driven.

We need an `ActionHistory` to keep track of the actions done by the player.
Not a mission history for now.

The `Brain` takes a `Mission` and generates an `Action`.

The `Planner` breaks down the Mission into sub-missions.
Which is an option that the `Brain` can choose if the mission is too complex.
And there is a `ActionPlan` that the `Brain` can choose to do, to trigger the replanning phase.

### Full loop

1. Observe the world
1. Think -> receive an Action
1. Convert the action to a request
1. Send the request to the world
1. Receive the response
1. Update the mission history

### Features

- [x] : World with renderer
    - [ ] : Prettier background with tiled grass
    - [ ] : Prettier terrain with tiled terrain types
    - [ ] : Prettier buildings with a big building in the center and a tiled garden
    - [ ] : Utensils can be held by the player
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
    - [x] : Different utensils
    - [ ] : Different buildings
- [ ] : Action object as an output of the Brain
- [ ] : Translate the map into a prompt
- [ ] : Convert the `to_prompts` into langchain objects using `PromptTemplate`s
- [ ] : Assign a mission to a player based on the map
    - [ ] : If a mission is too complex, break it down into sub-missions
    - [ ] : Share the mission with the world: the player can ask for help
- [ ] : Create an utensil to solve the mission
    - [ ] : If the utensil does not exist, create it
    - [ ] : Create an image of the utensil
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
    - factory - to create utensils
    - farm - to grow food
- utensils:
    - bucket
    - axe
    - hammer
    - hoe
