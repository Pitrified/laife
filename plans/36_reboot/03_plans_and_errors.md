---
status: done
---

# Phase 3 - Plans layout and errors

## Overview

Move all 27 old plan folders from `scratch_space/` into `plans/`, bring them to `plans.py check`, and fix the drifted errors that are not tooling.
Context: [`00_start.md`](00_start.md) D6, D12, D17, D18, Q5, Q8.

## Plan

- `git mv scratch_space/NN_name plans/NN_name` for the 27 numbered folders, as one commit with no content change, so git follows each file through the rename.
  The notebook in `12_action_structure` moves with its folder; the unnumbered folders (`async_`, `llm_`, `rebirth_`, ...) stay in `scratch_space/`.
- Second commit, the content:
  - a single-file folder's `README.md` becomes `00_start.md`;
  - every `00_start.md` gets `status`, `priority: 0` and a two-line `description`. Status comes from the folder's own text and from `plan.md`; a folder whose outcome cannot be told is `done` if the code it describes exists, and the uncertain ones are listed in the tracking log for the user;
  - 32, 34, 35: phase files and tracking tables brought to the status enum;
  - 31 and 33 keep their open status; 33 is brought up to date in phase 5;
  - the duplicate 22: `22_player_inventory` is renumbered to the next free number;
  - links between folders and from `scratch_space/rebirth_/` updated.
- Remove the plan citations from `src/laife/entities/sim_control.py` and `src/laife/meta/logger.py` (D17).
  Where the cited reason is needed, it goes into a doc under `docs/` and the docstring keeps only the rule.
- Update the references to `scratch_space/` plans in `ruff.toml`, `.gitattributes` and the instructions; `plans/` gets no lint ignores since it holds no Python, except the one notebook, which gets the scratch ignores.
- `.claude/settings.local.json`: drop the `rtk` entries. The file is not tracked, so this is a local edit only.
- Delete `.github/agents/draft-to-plan.agent.md` (D18).
- `ruff.toml`: add `scripts/*` per-file ignores as abyss has, now that `scripts/` exists.

## Done when

- `plans.py check --citations` passes over all folders.
- `make check` passes.
- `mkdocs build --strict` passes: no doc page linked into `scratch_space/`, checked during the survey, and it should stay that way.
