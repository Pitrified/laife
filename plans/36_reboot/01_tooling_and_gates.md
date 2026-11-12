---
status: done
---

# Phase 1 - Tooling and gates

## Overview

One fast `make check`, enforced by pre-commit, with a working editable-install target.
Context: [`00_start.md`](00_start.md) D3, D4, D5, D14, Q6, Q7.

## Plan

- `make sync` on g7, the first sync on this box. Builds pygame against the installed SDL2.
  Then run the existing `make test`, `make lint`, `make typecheck` to get a baseline before changing anything.
- Makefile, following abyss's:
  - every target except `sync` runs `uv run --no-sync`, so `dev-llm-core` holds;
  - `undev` reverts editable overrides (`uv sync --all-extras --all-groups`);
  - `check`: ruff check, ruff format --check, pyright, pytest, `plans.py check --citations`, and `mkdocs build --strict` if its measured time keeps `check` quick (Q6); otherwise it is `docs-check` on its own;
  - `hooks`: `uv run --no-sync pre-commit install`;
  - `nbstrip`: strips notebook outputs, since the hook only verifies;
  - `lint` reports and changes nothing; `format` applies.
- `.pre-commit-config.yaml` from abyss's, with `plans.py check` and the house-style scan (phase 2) as `local` hooks. No pytest in the hook (Q7).
  ruff and pyright pinned to the same versions in `pyproject.toml` and the hook config.
  `pre-commit`, `detect-secrets` and `nbstripout` added to the dev group.
  `.secrets.baseline` generated, `uv.lock` excluded as abyss does.
- `scripts/plans.py`: a copy of the skill's script, called by `check` and the hook.
  Until phase 3 moves the old folders in, `plans/` holds only 36, so `--citations` fails on the two `src/` citations; phase 3 fixes them, and `check` carries `--citations` from phase 3 on if phase 1 lands first.
- Fix the two scratch lint errors, and whatever the first repo-wide hook run finds, as their own commit.
- Time `make check` and the hook. Anything that makes them slow enough to be skipped moves out, per D5.

## Done when

- `make check` passes; each new gate shown failing once by a deliberate break.
- A commit with a lint error is refused by the hook.
- `make dev-llm-core` followed by `make test` still runs the editable llm-core.
- `mkdocs build --strict` passes, so `docs.yml` is unaffected.
