# Architecture

`lAIfe` separates pure game logic from the view and from the LLM reasoning.
Everything runs as concurrent asyncio tasks coordinated through queues.

## The three concurrent tasks

[`game/main.py`](https://github.com/Pitrified/laife/blob/main/game/main.py) builds the world and hands it to `serve_run` in [`laife.web.run`](../library/web.md), which runs three kinds of coroutine in one loop:

- the world simulation loop, one `WorldRunner.simulate`;
- the HTTP server that serves the world page, one uvicorn server;
- one `Player.play` per player.

The headless run hands its scripted world to the same `serve_run`.
The world and the players never call each other directly.
They communicate over asyncio queues, which keeps the logic side free of the view and lets players run independently.

## The world is the authority

The [`WorldRunner`](../library/entities.md) holds the canonical state: players, buildings, terrain.
A player can only change the world by sending a request and waiting for the answer.
The world validates every request, runs deterministic checks such as collision, and for build and craft actions asks an LLM judge whether the action is valid.
The world never tells a player what to do; it only answers requests.

This request and response contract is typed.
Requests and responses live in [`entities/world_channel.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_channel.py) as `WReq` and `WRes` subclasses, so payloads are validated at the boundary instead of passed as loose dicts.

## A player is an agent

A [`Player`](../library/entities.md) owns its position, state, inventory, and current mission.
Its decision making is delegated to its brain, which owns the LLM chains in [the llm package](../library/llm.md):
it picks the next action, breaks a hard mission into sub-missions, proposes a new mission, and answers messages from other players.
The player turns the chosen action into a world request and applies the response to its own state and mission history.

## The page observes, and only pauses

The server in [`laife.web`](../library/web.md) reads the runner's state into a snapshot and streams the structured log as events; the world page in `ui/world_web/` draws them in a browser.
It observes the world and does not change it. Its only controls are pause, resume, step and quit, which act on the turn gate and the server, not on the world's state.
See [Serving the world](../guides/web.md).

## Memory and grounding

Buildings, terrain, and utensils can be serialized to LangChain documents and stored in a vector store, so the brain can retrieve relevant world entities before deciding.

## Where to go next

- Follow one turn step by step in [the game loop guide](game_loop.md).
- See how each LLM call is built in [the LLM chains guide](llm_chains.md).
- See how environments and model providers are configured in [params and config](params_config.md).
