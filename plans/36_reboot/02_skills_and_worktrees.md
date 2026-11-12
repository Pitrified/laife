---
status: done
---

# Phase 2 - Skills and worktrees

## Overview

Copy klide's repo-local skills and the sibling-worktree script into laife.
Context: [`00_start.md`](00_start.md) D9, D11.

## Plan

- Copy `klide/.claude/skills/principles`, `deslopify` and `grill-me` into `.claude/skills/`.
  Adapt the text that names klide's own decisions (MD, AD ids, the frame gate) to laife or drop it.
  `grill-me` ends by writing a plan folder; point it at `plans/` and the tracked-development layout.
- Wire `deslopify`'s scanner, `house_rules` category only, into `make check` and the hook (phase 1 slot).
  The other categories stay advisory, as in klide.
- `scripts/spin_worktree` from `~/.claude/skills/sibling-worktree/scripts/spin_worktree`, with `REPO_SHORT=laife` and a `setup_repo` that runs `make sync` and links `~/cred/laife/.env` if needed.
- Confirm in a fresh session that the three skills register: a skill written mid-session does not appear until the next one (klide, 2026-09-16).

## Done when

- The three skills appear in a fresh session's skill list.
- The house-style scan refuses a file with an em dash.
- `scripts/spin_worktree` opens a worktree, its `make check` passes, and the worktree is closed by the skill's runbook.
