---
status: done
---

# Phase 4 - Agent instructions

## Overview

`CLAUDE.md` and a rewritten `.github/copilot-instructions.md` that describe the repo as phases 1 to 3 left it.
Context: [`00_start.md`](00_start.md) D1, D2, D7, D8, D10, D14.

## Plan

- `CLAUDE.md`: the import line and the short Claude Code note, as in the siblings.
- `.github/copilot-instructions.md`, keeping the architecture and key-patterns sections, and adding:
  - "How to write", from klide (it includes the mannered-writing paragraph house-renderer lacks), plus house-renderer's comment rules: no history, no plan citations, no counts.
  - "Planning", as in both.
  - "How to build", adapted: laife's driver is the game loop and the LLM, so the house-renderer point about the conversation being the driver does not carry over. Keep small primitives, no knobs without a case.
  - "The mechanical checks": `make check` before every commit, the hook is installed with `make hooks`, never `--no-verify`, a skipped test is not a passed test, `uv run --no-sync`.
  - "Running the engine": the engine running is the evidence, in planning and in implementation (D8). Until a headless harness exists (a `plan.md` item), the rule names what exists today and the gap.
  - "Unattended work": planning is cooperative with the user; only a `planned` phase with no open `NEW_ANS` runs unsupervised, on a feature branch, no new dependencies, `make check` green per commit, no merge to `main`; prompt versions and data models change only where the phase plan names it (D7, D19).
  - "Which box": g7 and g4 (D10), with the hostname check house-renderer uses.
  - "Plans": `plan.md` is the unnumbered backlog; picking an item creates a numbered `plans/NN_name/` folder by tracked-development; `plans.py`.
  - Docstrings: Google style, pointing at the global Python rule rather than restating it.
- Fix the Python version (3.14) and the ruff target line.
- Run the deslopify scan, all categories, over both files and triage.

## Done when

- A fresh session in the repo shows the instructions loaded.
- Every command the instructions name runs.
- `make check` passes.
