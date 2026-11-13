# web

The world served over HTTP.
Source: [`src/laife/web/`](https://github.com/Pitrified/laife/tree/main/src/laife/web).
How to run it and what the routes return: [the serving guide](../guides/web.md).
Nothing here imports pygame.

- [`snapshot.py`](https://github.com/Pitrified/laife/blob/main/src/laife/web/snapshot.py) - `WorldSnapshot` and `take_snapshot`, the world as JSON. Players get a `PlayerView`, since `Player` is not a pydantic model.
- [`events.py`](https://github.com/Pitrified/laife/blob/main/src/laife/web/events.py) - `EventHub`, which numbers events and fans them out, and `add_log_sink`, which feeds it from the structured log.
- [`server.py`](https://github.com/Pitrified/laife/blob/main/src/laife/web/server.py) - `create_app`, the FastAPI routes, and `serve`, which runs uvicorn as a task in the game's loop.

Every route is `async def`: FastAPI runs a plain `def` route in a worker thread, which would read the game state from outside the event loop.
