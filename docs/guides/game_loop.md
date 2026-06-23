# Game loop

One turn of a player, from perceiving the world to applying the world's answer.
The pieces referenced here are documented in [the entities library page](../library/entities.md) and [the llm library page](../library/llm.md).

## The turn

A player turn follows six steps.

1. Observe the world.
   The player sends an observe request; the world returns a structured snapshot of nearby entities centred on the player.
2. Think.
   The brain receives the observation and the current mission and returns a single action.
3. Convert the action to a request.
   The chosen action becomes a typed world request.
4. Send the request to the world.
   The request goes onto the world input queue; the player awaits the response.
5. Receive the response.
   The world validates, runs collision or an LLM judge as needed, mutates its state on success, and returns a typed response.
6. Update the mission history.
   The player records the action and the world's feedback, then loops.

## Observation

The observation is a [`WorldMapObservation`](../../src/laife/entities/world_map_observation.py).
It lists nearby entities with their type, name, relative position, and distance, and renders to text for the prompt with directions like "to the south".
Positions are converted to cardinal directions relative to the observer, so the LLM reasons in spatial language rather than raw coordinates.

## Actions

The brain returns one [`BaseAction`](../../src/laife/entities/action.py) subclass: move, build, craft, interact, complete, or plan.
Each action carries a `reason` and the fields specific to it.
Actions are intentions, not guarantees: a good action moves the mission forward, possibly across several turns.

## Requests and responses

Requests and responses are defined in [`entities/world_channel.py`](../../src/laife/entities/world_channel.py).
Every response carries a status, and concrete subclasses carry typed payloads, for example a build response, a craft response, or an error.
Movement is special: a move is applied in steps, each validated by the deterministic collision check, so a player cannot walk through a building.

## Validation and judging

Deterministic rules, such as collision between axis-aligned boxes, are checked by the world directly.
Whether a build or craft actually satisfies the mission is a judgement call, so the world delegates it to an LLM judge in [`entities/world_judge.py`](../../src/laife/entities/world_judge.py).
The judge's verdict and feedback flow back to the player as part of the response.

## Missions

A mission has an objective, a history of actions and results, and a status.
When a mission is too complex the brain can choose the plan action, which triggers the [planner](llm_chains.md) to split it into sub-missions with the accumulated history as extra context.
On success the mission is marked complete; after repeated failures it is marked failed and a new mission is generated.
