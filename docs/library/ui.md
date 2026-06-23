# ui

Real-time console feedback.
Source: [`src/laife/ui/`](../../src/laife/ui).

## Async console logger

[`alog.py`](../../src/laife/ui/alog.py) defines `Alog`, a singleton asynchronous logger reachable through the `alg` instance.
It queues messages and collapses repeats by counting occurrences, so a noisy game loop stays readable.

This is the live, human-facing channel.
The persisted, machine-readable log for later analysis is [the structured logger](meta.md).
