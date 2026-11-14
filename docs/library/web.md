# web

The world served over HTTP.
Source: [`src/laife/web/`](https://github.com/Pitrified/laife/tree/main/src/laife/web).
How to run it and what the routes return: [the serving guide](../guides/web.md).
Nothing here imports pygame.

- [`snapshot.py`](https://github.com/Pitrified/laife/blob/main/src/laife/web/snapshot.py) - `WorldSnapshot` and `take_snapshot`, the world as JSON. Players get a `PlayerView`, since `Player` is not a pydantic model.
- [`events.py`](https://github.com/Pitrified/laife/blob/main/src/laife/web/events.py) - `EventHub`, which numbers events and fans them out, and `add_log_sink`, which feeds it from the structured log.
- [`vendor.py`](https://github.com/Pitrified/laife/blob/main/src/laife/web/vendor.py) - the `ui/vendor.toml` manifest, `make vendor`'s download, hash check and extraction, and the lock check before a file is served.
- [`server.py`](https://github.com/Pitrified/laife/blob/main/src/laife/web/server.py) - `create_app`, the FastAPI routes, and `serve`, which runs uvicorn as a task in the game's loop and stops it, by the quit route or a signal, after closing the hub's streams.

The page itself is in `ui/world_web/`, outside the package, served by `create_app`; the sprite table it reads is `laife.config.sprites`.

Every route is `async def`: FastAPI runs a plain `def` route in a worker thread, which would read the game state from outside the event loop.
