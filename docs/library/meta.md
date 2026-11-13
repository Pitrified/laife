# meta

Cross-cutting support utilities.
Source: [`src/laife/meta/`](https://github.com/Pitrified/laife/tree/main/src/laife/meta).

## Structured logger

[`logger.py`](https://github.com/Pitrified/laife/blob/main/src/laife/meta/logger.py) configures a loguru JSON-lines file sink, written asynchronously so the game loop is not blocked.
Call `configure_logging` once at startup, before the asyncio loop, then bind events at call sites with `slog`.
`log_llm_call` is the `on_call` of every game chain; it writes the `llm_call` record, with player and turn from the log context (see [the LLM chains guide](../guides/llm_chains.md#timing)).
This is the analysis and debugging log; the real-time console feedback channel is [the ui logger](ui.md).

[`log_events.py`](https://github.com/Pitrified/laife/blob/main/src/laife/meta/log_events.py) holds the event-name constants used when binding log records: actions, world requests and responses, mission transitions, and LLM calls and results.
Using shared constants keeps event names consistent across the codebase so logs stay queryable.
