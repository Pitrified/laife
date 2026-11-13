---
status: done
---

# Phase 2 - Dependency upgrade, llm-core then laife

## Overview

`langchain_core` 1.2.14, the version in `uv.lock`, imports `pydantic.v1` at import time and warns that it is incompatible with Python 3.14.
langchain-core 1.8.0 imports it lazily and does not warn (checked 2026-11-13 in a scratch venv: `import langchain_core.language_models, langchain_core.prompts` with `-W always`).
The fix is the upgrade, not a filter.
The rest of the lock is months old too, so the whole lock moves, not only langchain-core.
Context: [`00_start.md`](00_start.md).

`uv lock --upgrade --dry-run` in laife (2026-11-13) shows these major jumps among others:
openai 2 to 3, transformers 4 to 5, sentence-transformers 5 to 6, protobuf 6 to 7, rich 14 to 15, python-dateutil 2 to 4, the torch CUDA wheels moving from cu12 to cu13.
langchain 1.2 to 1.5, langchain-openai 1.1 to 1.7, langgraph 1.0 to 1.2 stay within their majors.

## Plan

### llm-core

llm-core plans this as its own effort, `scratch_space/07_deps_update/` in that repo, on branch `chore/deps-update`.
It was phase 3 of the Gemini effort; the user split it out and deferred Gemini (2026-11-13).

- `uv lock --upgrade`, sync, llm-core's suite; fix what the upgrade breaks, recorded in that phase file.
- Release 0.3.0: version bump, `CHANGELOG.md` entry, a tag, as the v0.2.2 release commit did. Lower bounds raised only where the code needs it.
- A guide in llm-core's `docs/guides/` for dependents: what changed for them, and that the old tag keeps working until they move.
  Dependents may break; they keep the old pin until their own upgrade pass.
- The push of the branch and of the tag is the user's, from g4.

### laife

- Pin the new llm-core tag in `pyproject.toml`, `uv lock --upgrade`, `make sync`.
- `make check`, `make headless`; the pydantic warning is expected to drop out of the test warnings.
- `make run` on g4 by the user: the live provider path is the one an upgrade of openai and langchain-openai can break, and headless does not call it.

## Out of scope

- The exactly pinned tools (ruff, pyright, nbstripout, detect-secrets) and their hook revs.
- Other repos depending on llm-core.

## Done when

- llm-core: suite green on the new lock, tagged, guide written.
- laife: on the new tag and lock, `make check` passes, `make headless` runs, the pydantic warning is gone from the test run.

## Outcome

- llm-core `v0.3.0` released (its folder `07_deps_update`), pushed by the user.
- laife relocked with `uv lock --upgrade` while still pinned to `@v0.2.2`; the exactly pinned tools did not move. No code change.
  `make check` passes; test warnings 27 to 15, the pydantic one gone.
  The rest: pygame's AVX2 notice (phase 3, parked) and `asyncio.iscoroutinefunction` deprecations from chromadb and langsmith, upstream.
- `make headless` runs and ends at the same positions as before the upgrade.
- Pinned `@v0.3.0`, `uv lock --upgrade-package llm-core`: `make check` and `make headless` pass, same warnings and positions as on the relock.
- Not verified: the live provider path on openai 3 and langchain-openai 1.7; `make run` on g4 by the user.
