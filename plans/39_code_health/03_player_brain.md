---
status: draft
---

# Phase 3 - the thinking moves into `PlayerBrain`

## Overview

`PlayerBrain` becomes the player's thinking layer: it owns the four player chains, and `Player` asks it.
The mind state stays on `Player`. Context: [`00_start.md`](00_start.md), Q3.

## Plan

Draft.

- `PlayerBrain` builds the action, planner, replier and mission chains from one config holding the chat config and a `PromptLoaderConfig` per chain (Q5).
- Its methods take what the call needs from the player and return the parsed result: `next_action`, `plan`, `propose_mission`, `reply`. Names are settled while editing.
- The input building and `timed_llm_call` move from `Player` into these methods, so all four calls are timed the same way.
- `Player` keeps the body, the turn loop, world I/O and the mind state; `think`, `plan`, `_generate_mission_objective` and `receive_message` call the brain and apply the result.
- `receive_message` stays free of world I/O; `brain.reply` does no world I/O either.
- The existing wrappers stay as the brain's internals in this phase; phase 4 removes them.
- Tests for the thinking go to the brain level, with the chat model scripted, and no queues; `Player` tests mock the brain.

One player instance, one brain instance. Whether they share a mind state is a backlog item, not this phase.

## Done when

- `Player` builds no chain and calls no chain directly.
- `make check` passes; `make headless` gives the same positions as on `main`.
