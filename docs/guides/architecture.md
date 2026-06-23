# Architecture

`lAIfe` separates pure game logic from rendering and from the LLM reasoning.
Everything runs as concurrent asyncio tasks coordinated through queues.

## The three concurrent tasks

[`game/main.py`](https://github.com/Pitrified/laife/blob/main/game/main.py) starts three kinds of coroutine with `asyncio.gather`:

- the world simulation loop, one `WorldRunner.simulate`;
- the renderer, one `WorldRenderer.render`;
- one `Player.play` per player.

The world and the players never call each other directly.
They communicate over asyncio queues, which keeps the logic side free of pygame and lets players run independently.

## The world is the authority

The [`WorldRunner`](../library/entities.md) holds the canonical state: players, buildings, terrain.
A player can only change the world by sending a request and waiting for the answer.
The world validates every request, runs deterministic checks such as collision, and for build and craft actions asks an LLM judge whether the action is valid.
The world never tells a player what to do; it only answers requests.

This request and response contract is typed.
Requests and responses live in [`entities/world_channel.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_channel.py) as `WReq` and `WRes` subclasses, so payloads are validated at the boundary instead of passed as loose dicts.

## A player is an agent

A [`Player`](../library/entities.md) owns its position, state, inventory, and current mission.
Its decision making is delegated to the LLM chains in [the llm package](../library/llm.md):
the brain picks the next action, the planner breaks a hard mission into sub-missions, and the replier answers messages from other players.
The player turns the chosen action into a world request and applies the response to its own state and mission history.

## Rendering observes, never mutates

The [`WorldRenderer`](../library/rendering.md) reads the runner's state and draws it with pygame.
It is a view layer: it observes the world but does not change it, so the simulation behaves the same with or without a window.

## Memory and grounding

Buildings, terrain, and utensils can be serialized to LangChain documents and stored in a vector store, so the brain can retrieve relevant world entities before deciding.
The embedding wrapper lives in [the embed package](../library/embed.md).

## Where to go next

- Follow one turn step by step in [the game loop guide](game_loop.md).
- See how each LLM call is built in [the LLM chains guide](llm_chains.md).
- See how environments and model providers are configured in [params and config](params_config.md).
