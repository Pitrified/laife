---
status: done
---

# Phase 4 - Singleton, release and pin

## Overview

laife drops its copy of `Singleton`; llm-core releases v0.4.0 and laife pins it. Context: [`00_start.md`](00_start.md), Q1 and Q5.

## Steps

laife:

- `LaifeParams` and `Alog` import `Singleton` from `llm_core.metaclasses`; `src/laife/meta/singleton.py` is deleted, with its test if one exists.
- Docs: `docs/library/meta.md` loses the Singleton section, including its line on clearing the registry in tests; `docs/guides/params_config.md` links to llm-core's; the line on resetting the singleton in `docs/guides/docs_maintenance.md` goes.
- `plan.md`: "Singleton reset" removed; the reset, if ever needed, is llm-core's.

llm-core:

- v0.4.0: version in `pyproject.toml`, CHANGELOG `Unreleased` becomes `[0.4.0]`, `uv lock --offline`; merge `feat/v0_4_items` to `main`, annotated tag `v0.4.0`. The push is the user's.

laife, after the user has pushed the tag:

- `pyproject.toml` pins `@v0.4.0`, `uv lock`, `make undev`; the lock moves only llm-core.

## Done when

- `make check` passes on the pinned tag, and `make headless` ends at the same positions as after phase 3.
- Folder 40 done.

## Decided by the agent while implementing

For the user's review, 2026-11-13.

- No laife test covered `Singleton`, so none was deleted.
- llm-core's `docs/index.md` lists the `on_call` callback and the scripted model, and `testing/` in the layout.
- llm-core `feat/v0_4_items` was fast-forwarded into llm-core `main` and tagged there, as this file planned; the branch is kept.

## Outcome

- laife 7837b4f: `LaifeParams` and `Alog` use llm-core's `Singleton`; the copy, its docs section and the docs line on clearing it are gone; `plan.md` "Singleton reset" removed. `make check` passes, 272; `make headless` same positions and per-player records as phase 3.
- llm-core 84340e0 "chore: release v0.4.0": version, CHANGELOG `[0.4.0]`, lock, docs index. `main` fast-forwarded to it, annotated tag `v0.4.0`. 207 tests pass; pyright shows the same transcription errors as before.
- The user pushed llm-core `main` and `v0.4.0`.
- After the user's push (the GitHub tag resolves to 84340e0): laife pins `@v0.4.0`; `uv lock` moved only llm-core; `make undev` replaced the editable install. `make check` passes, 272; `make headless` ends at the same positions with the same per-player records as before the pin.
