# lAIfe

Let's make AI rule the world!

## Run the game

```bash
uv run game/main.py
```

press `q` to quit the game.

## Setup

Check the [CONTRIBUTING.md](CONTRIBUTING.md) for instructions on how to set up the local development environment.

## Documentation

The full documentation lives in [`docs/`](docs/README.md): guides on the architecture, the game loop, the LLM chains, and configuration, plus a per-module library reference.
It is published as a site at https://pitrified.github.io/laife/, rebuilt on every push to `main`.
See [`docs/README.md`](docs/README.md) for how to build and serve it locally.

## Ideas

There are players, that do things in the environment via actions.

Players have states.

There are objects in the environment.

The players can interact with the objects, and with each other.

A player has a main mission.
If a player has nothing to do, it can interact with the environment to find a mission.
To complete the mission, the player has to interact with the environment.

A mission can be solved in several steps.
Missions can be nested.

If an utensil is needed to solve a mission, the player has to find the utensil first.
If the utensil does not exist, the player has to create it, which is a mission in itself.

New building blocks can be created by the players, again as a mission.

World entities:

- Player
- Building
  - which can be things like a factory/farm/house but also chest/tree/rock
  - some buildings can be one over the other, like a tree in a forest, or a chest in a house
- Utensil
- Terrain
  - A terrain is an entire section of map
  - Default background is grass
  - When building the prompt, the area of each type of terrain is calculated
    and described

Game logic is dynamic:
given a mission, the player decides which utensil to use, and where to go to use it.
The engine checks that the player has the utensil,
the LLM checks that the utensil can be used in the location to solve the mission.

In general,
the player can send requests to the world to do some action,
and the world answers with the result.
The world never tells the player what to do.

In `to_prompt` there could be a position parameter,
so that in the prompt the location of other entities is dynamically converted to text eg "to the south",
by the world.

A player in the beginning does not know the world.
One of the option is to explore (well actually just move, but with purpose).

A mission has an objective, a history of actions, and a status (done, failed, in progress).
There can be sub-missions, and the nesting level is tracked.

The chosen action is validated by the world, it must exist as an option, and be possible in the current state of the world.
The world answers with a feedback, which is placed in the history of the mission.
The player LLM iterates on the mission with more history, and can pick a different action.
One of the player LLM response option is to split the mission into sub-missions.

The validation of whether an action actually solves the mission is done by the world LLM,
this is one of the possible feedback.

The `Brain` thinks about a `Mission` and generates an `Action`.

All the action except `move` are done as world requests.
Actually `move` is also a world request, but has to be handled in `move_delta` steps,
each one has to be validated by the world with deterministic collision system.
Whether the player thinks again after a certain number of steps, or after each step, or after each failed step, is to be decided.

Add a langchain `tool` to compute distance between two points on the map.
Which is something that the player can use to decide where to go precisely to solve the mission,
generating something more specific than `ActionMove`.

Add decorators to player functions to update the state of the player.
So something like `@update_state(PlayerState.MOVING)` on the `move` function,
so that the state is automatically updated when the function is called and ends.

The `Mission` do not need a `MissionType`, it has to be inferred from the mission description.
This is because missions can be very dynamic and complex, world/brain driven.

We need an `ActionHistory` to keep track of the actions done by the player.
Not a mission history for now.

The `Planner` breaks down the Mission into sub-missions.
There is an action `ActionPlan` that the `Brain` can choose to do, to trigger the replanning phase,
if the mission is too complex and it failed some times maybe.
The new planning will have more feedback received in the history.

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
  - [x] : Make the list of possible player actions: base done, easily extendable with new actions
- [ ] : Map of the world with entities:
  - [x] : Different buildings
  - [ ] : Different terrain
  - [ ] : Make the map dynamic with some kind of loader
- [ ] : Vector db of the world entities
  - [x] : Different utensils
  - [ ] : Different buildings
  - [ ] : Different terrains
- [ ] : Action object as an output of the Brain
- [ ] : Translate the map into a prompt
- [ ] : Convert the `to_prompts` into langchain objects using `PromptTemplate`s
- [ ] : Assign a mission to a player based on the map
  - [ ] : If a mission is too complex, break it down into sub-missions
  - [ ] : Share the mission with the world: the player can ask for help
- [ ] : Create an utensil to solve the mission
  - [ ] : If the utensil does not exist, create it
  - [ ] : Create an image of the utensil --> need wrapper for langchain image generation tools
- [ ] : Solve the mission
- [ ] : The mission could be building a building
- [ ] : Add an alive parameter to the player
- [ ] : Let players interact with each other with
   - [ ] : a `ActionInteract` action 
   - [ ] : a `to_prompt` that describes the other player in the prompt
- [ ] : Add a player inventory
- [ ] : Add a player long term memory
- [ ] : Check why some classes are dataclasses and some are pydantic models, and unify the approach
- [ ] : Add typed `WResXXX` classes for world responses, instead of the generic `WRes` with a dict payload
   Or at least define schemas for the payloads of the different world responses, build the payloads as pydantic models and validate when receiving them.
   And we can maybe just use `response: BaseModel` in `WRes`, and just have the different schemas defined.
- [x] : Add an ActionPickerInput BaseModelKw, receive that in invoke; required prompt vars can be inferred from the fields of the input model and the prompt template loaded can be validated to ensure it contains them all.
- [ ] : Make the vector-able entities uniform, so that we have common ways to build the prompt and place them in the vector db
- [ ] : Add a structured logger with a whole bunch of info from the game loop/missions/actions, to be able to analyze the game play and debug better
   - [ ] : Add a dashboard to visualize the logs and analyze the game play
   - [ ] : Enhance UI of game window to show more info, also interactive with mouse
- [ ] : The sending requests and receiving responses in player is quite repetitive, optimize it
- [ ] : The action picker and world judge are quite similar, try to create a superclass

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
