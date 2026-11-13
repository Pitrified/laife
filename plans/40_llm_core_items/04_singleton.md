---
status: planned
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
