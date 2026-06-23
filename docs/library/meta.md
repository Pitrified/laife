# meta

Cross-cutting support utilities.
Source: [`src/laife/meta/`](../../src/laife/meta).

## Singleton

[`singleton.py`](../../src/laife/meta/singleton.py) defines the `Singleton` metaclass.
A class using it has exactly one instance per process; the params singleton uses it.
In tests, reset shared state by clearing the metaclass instance registry.

## Structured logger

[`logger.py`](../../src/laife/meta/logger.py) configures a loguru JSON-lines file sink, written asynchronously so the game loop is not blocked.
Call `configure_logging` once at startup, before the asyncio loop, then bind events at call sites with `slog`.
This is the analysis and debugging log; the real-time console feedback channel is [the ui logger](ui.md).

[`log_events.py`](../../src/laife/meta/log_events.py) holds the event-name constants used when binding log records: actions, world requests and responses, mission transitions, and LLM calls and results.
Using shared constants keeps event names consistent across the codebase so logs stay queryable.
