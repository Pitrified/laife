# entities

The world model and everything in it.
Source: [`src/laife/entities/`](https://github.com/Pitrified/laife/tree/main/src/laife/entities).
This package is pure logic with no pygame dependency.

## The world runner

[`world_runner.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_runner.py) defines `WorldRunner`, the authority over world state.
It owns the players, buildings, and terrain, and exposes the simulation loop.
It reads requests from its input queue, validates them, mutates state on success, and returns a typed response.
Build and craft requests are sent to the LLM judge; movement is applied step by step with collision checks; interactions are routed between players.

## The world channel

[`world_channel.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_channel.py) defines the typed contract between players and the world.
Requests are `WReq` subclasses, one per action: build, craft, move, observe, interact, complete.
Responses are `WRes` subclasses carrying a status and a typed payload, plus an error response.
This replaces loose dict payloads with validation at the boundary.

## Players

[`player.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/player.py) defines `Player` and `PlayerState`.
A player holds its position, state, inventory, and current mission, and runs its own turn loop.
It delegates decisions to [the LLM chains](llm.md), converts the chosen action into a world request, and applies the response to its own state and mission history.

## Actions

[`action.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/action.py) defines `BaseAction` and the concrete actions the brain can choose, along with the action picker chain and its input model.
Every action carries the reason it was chosen.

## Buildings, terrain, utensils

- [`building.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/building.py) and [`building_types.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/building_types.py) - a `Building` instance and its `BuildingType` master data, with the starter building types.
- [`terrain.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/terrain.py) and [`terrain_types.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/terrain_types.py) - terrain regions and their types.
- [`utensil.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/utensil.py) - tools a player can hold and use.

These entities render to prompt text relative to a point of view, and serialize to and from LangChain documents so they can be stored in the vector store.

## Observation and judging

- [`world_map_observation.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_map_observation.py) - the structured spatial snapshot a player perceives, with relative positions and cardinal directions.
- [`world_judge.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_judge.py) - the LLM judge that decides whether a build or craft action is valid.

## Utilities

[`utils/`](https://github.com/Pitrified/laife/tree/main/src/laife/entities/utils) holds geometry and direction helpers: axis-aligned box collision in [`geometry.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/utils/geometry.py) and cardinal-direction conversion in [`directions.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/utils/directions.py).

## See also

- [The game loop guide](../guides/game_loop.md) for how these pieces interact in one turn.
- [The llm library page](llm.md) for the reasoning side.
