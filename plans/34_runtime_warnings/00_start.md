# runtime warnings cleanup - bootstrap

Spun out of the observability effort:
[`32_observability/05_random_warnings.md`](../32_observability/05_random_warnings.md)
collected three startup/shutdown warnings seen on real `make run` sessions.
None of them affects gameplay; each is a small independent bugfix.

## The three warnings

### 1. SystemExit on quit

```log
W: Quitting the game
Task exception was never retrieved
future: <Task finished name='Task-1' coro=<main() ...> exception=SystemExit()>
```

Root cause (read, not guessed): `WorldRenderer.quit()`
(`src/laife/rendering/world_renderer.py:128`) calls `pygame.quit()` then `sys.exit()`.
`sys.exit()` raises `SystemExit` inside the renderer coroutine,
which is one of several tasks in `asyncio.gather(...)` in `game/main.py::main`.
The exception cancels the gather but asyncio reports it as an unretrieved task exception
instead of a clean shutdown.
The fix is a cooperative shutdown: signal the other tasks (cancel the gather,
or a shared stop event) instead of `sys.exit()` from inside a task.

### 2. pydantic V1 shim warning on Python 3.14

```log
.venv/.../langchain_core/_api/deprecation.py:25: UserWarning:
Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.
```

Comes from `langchain_core` importing `pydantic.v1` shims, not from our code.
Options: upgrade langchain-core to a version that dropped the v1 shims,
or suppress that specific warning at startup with a comment naming the upstream issue.
Needs a check of what version we pin and what upstream has fixed.

### 3. pygame AVX2 build warning

```log
RuntimeWarning: Your system is avx2 capable but pygame was not built with support for it.
```

Cosmetic performance note from the pygame wheel.
Options: try a wheel/build with AVX2 (`PYGAME_DETECT_AVX2=1` at compile time,
which we do not control for prebuilt wheels), switch to `pygame-ce`,
or suppress/accept the warning.
Lowest priority of the three.

## Decisions

- One folder for all three: they share a theme (noise on startup/shutdown of `make run`)
  and are each too small to track alone.
- One phase per warning, ordered by value: the quit path is a real (if harmless) bug,
  the other two are dependency noise.
- Suppression is an acceptable outcome for warnings 2 and 3 if a real fix is not
  reachable from our side; the phase doc must then name the upstream issue.

## Open questions

- Warning 2: which langchain-core version drops the pydantic v1 import on py3.14,
  and can we move to it without touching the llm_core migration?
- Warning 3: is `pygame-ce` a drop-in for our usage, and do we care about blit
  performance at all at this scale?
