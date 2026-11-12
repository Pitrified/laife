---
status: done
---

# Phase 5 - Assessment and backlog

## Overview

Bring folder 33's assessment up to date against the code and leave it open, and make `plan.md` the single unnumbered backlog.
Context: [`00_start.md`](00_start.md) D8, D13, D20.

## Plan

- Folder 33 (moved into `plans/` by phase 3): check each finding against the code as it stands.
  Folders 34 and 35 came after it, so some may be resolved. Each finding is marked still true, resolved (with where), or wrong, in place.
  The status stays open; it is not closed by this phase.
- `plan.md`:
  - fold in the README todo list; items already done are dropped rather than copied;
  - add the open findings of 33 that are work to do, as items pointing back at 33;
  - add the engine items from D8: a headless run of the real engine with a scripted or recorded LLM, usable as a gate; and whether pygame stays as the renderer, against a text-only runner (`scratch_space/rebirth_/`) or a web app served from g7.
  - Items carry no folder numbers. A short note at the top says how an item becomes a folder.
- `README.md`: the todo list replaced by a link to `plan.md`.

## Done when

- Every finding in 33 has a current verdict.
- Every unchecked README todo is either in `plan.md` or recorded as done.
- `make check` passes.
