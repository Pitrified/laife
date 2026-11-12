# Worktrees

A second branch can be worked in its own git worktree beside the main one, with its own Claude session.
The general procedure, opening and closing, is the `sibling-worktree` skill in the dotfiles;
this page holds only what is particular to laife.

## Opening one

From the main worktree:

```bash
scripts/spin_worktree feat/NN_name      # -> ../laife-NN
```

The script adds the worktree, runs `make sync` in it, and starts Claude in a zellij session named `wt-laife-NN-name`.
Each worktree has its own `.venv`; uv's cache is shared, so the second sync links files rather than downloading them.

## What the worktrees share

- **Credentials**: `~/cred/laife/.env`, outside the repository, read by every worktree. Nothing is linked.
- **Logs**: `cache/` is gitignored and per worktree, so `make tui` in a worktree reads that worktree's runs.
- **llm-core**: `make dev-llm-core` installs into the current worktree's `.venv` only.

## Conflict files

- `plan.md`: two branches picking items from the backlog both edit it. Merge by hand, keeping both edits.
- `plans/`: a folder number claimed on two branches. `python3 scripts/plans.py branches` shows the collision.

## After a merge

Nothing beyond the skill's runbook: `make check` on `main`, then close the worktree.
