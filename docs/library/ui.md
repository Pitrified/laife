# ui

Real-time console feedback.
Source: [`src/laife/ui/`](https://github.com/Pitrified/laife/tree/main/src/laife/ui).

## Async console logger

[`alog.py`](https://github.com/Pitrified/laife/blob/main/src/laife/ui/alog.py) defines `Alog`, a singleton asynchronous logger reachable through the `alg` instance.
It queues messages and collapses repeats by counting occurrences, so a noisy game loop stays readable.

This is the live, human-facing channel.
The persisted, machine-readable log for later analysis is [the structured logger](meta.md).
