# meta

Cross-cutting support utilities.
Source: [`src/laife/meta/`](https://github.com/Pitrified/laife/tree/main/src/laife/meta).

## Singleton

[`singleton.py`](https://github.com/Pitrified/laife/blob/main/src/laife/meta/singleton.py) defines the `Singleton` metaclass.
A class using it has exactly one instance per process; the params singleton uses it.
In tests, reset shared state by clearing the metaclass instance registry.

## Structured logger

[`logger.py`](https://github.com/Pitrified/laife/blob/main/src/laife/meta/logger.py) configures a loguru JSON-lines file sink, written asynchronously so the game loop is not blocked.
Call `configure_logging` once at startup, before the asyncio loop, then bind events at call sites with `slog`.
This is the analysis and debugging log; the real-time console feedback channel is [the ui logger](ui.md).

[`log_events.py`](https://github.com/Pitrified/laife/blob/main/src/laife/meta/log_events.py) holds the event-name constants used when binding log records: actions, world requests and responses, mission transitions, and LLM calls and results.
Using shared constants keeps event names consistent across the codebase so logs stay queryable.
