---
status: draft
---

# Phase 2 - pydantic v1 warning

## Overview

`langchain_core` imports `pydantic.v1` shims at startup and warns that
core pydantic V1 functionality is incompatible with Python 3.14+.
Not our code; the fix is a dependency move or a targeted suppression.
Context: [`00_start.md`](00_start.md).

## Goals

1. `make run` startup no longer prints the pydantic V1 UserWarning.

## Plan

- Check the pinned `langchain-core` version and its changelog for the release
  that drops the `pydantic.v1` import path.
- If an upgrade is compatible with the current `llm_core` usage, bump it and
  run the suite.
- If not, add a `warnings.filterwarnings` scoped to that exact message in
  `configure_logging` (or the game entrypoint), with a comment naming the
  upstream issue and the condition for removing the filter.

## Out of scope

- Any broader langchain upgrade or migration work.

## Done when

- The warning is gone from a real `make run` startup.
- Project verification suite passes.
