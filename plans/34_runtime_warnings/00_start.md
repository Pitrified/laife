---
status: done
priority: 0
description: |
  Noise and waste a run shows: the pydantic V1 warning, fixed by a dependency upgrade through llm-core, and the build judge paid before the free collision check.
  `SystemExit` on quit and pygame's AVX2 notice are parked with the renderer question.
---

# runtime warnings cleanup - bootstrap

Spun out of the observability effort:
[`32_observability/05.1_random_warnings.md`](../32_observability/05.1_random_warnings.md)
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

## Decisions 2026-11-13

Taken with the user.

- Only what the headless run verifies is in scope now: the judge order (phase 4) and the pydantic warning (phase 2).
  Phases 1 and 3, `SystemExit` on quit and the AVX2 notice, are parked: they live in the renderer, and pygame or a web app is still an open point in `plan.md`.
- Order: phase 4, then phase 2.
- The judge order joins this folder from the backlog: it is the same theme, a run doing something it should not, here paying for a judge call that cannot change the outcome.
- Warning 2 is fixed by upgrading, not filtered: langchain-core 1.8.0 no longer warns on import (checked in a scratch venv).
  The answer to the open question above.
- The upgrade covers the whole lock, which is months old, and goes through llm-core:
  upgrade llm-core, release a new tag, write a guide for its dependents, then move laife to the tag.
  Other dependents may break and keep the old pin until their own upgrade pass; llm-core is 0.x for this reason.
- llm-core already plans its lock refresh, as phase 3 of its Gemini effort; phase 2 here runs that phase rather than writing a second one.

## Open questions 2026-11-13

- Q1: the new llm-core version. 0.3.0, since dependents may break, or 0.2.3?
- Q2: llm-core's lower bounds in `pyproject.toml` (`langchain-core>=0.3` and so on).
  Raise them to the versions the new lock was tested with, or leave them and raise only what the code needs?
- Q3: the Gemini effort's phase 3 says to bump laife in its phase 5, with Gemini.
  Running the refresh alone now moves laife ahead of that; its phase file needs a line saying so.

## Answers 2026-11-13

- Q1: 0.3.0.
- Q2: raise only what the code needs.
- Q3: the dependency update is split out of the Gemini effort in llm-core as its own folder, `07_deps_update`; Gemini is deferred and replanned there.

## State 2026-11-13

Phases 4 and 2 are done. What is left, phases 1 and 3, is parked with the renderer question, so the folder goes back to `draft` until that is decided.

## State 2026-11-14

Phases 1 and 3 are discarded: pygame left the repo in `41_renderer_choice` phase 5. The folder is done.
