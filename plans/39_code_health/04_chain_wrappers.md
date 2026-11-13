---
status: draft
---

# Phase 4 - chain wrappers

## Overview

Use llm-core's `StructuredLLMChain` directly instead of the five laife wrappers. Context: [`00_start.md`](00_start.md), Q1 and Q5.
Runs after phase 3, so the player chains are already inside `PlayerBrain`.

## Plan

Draft.

- Remove `ActionPicker`, `WorldActionJudge`, `MissionGenerator`, `PlayerPlanner`, `PlayerReplier`; keep the input and output models.
- `PlayerBrain` and `WorldRunner` hold `StructuredLLMChain[...]` attributes, each built from a `PromptLoaderConfig` loaded with `PromptLoader` (Q5: the config stays, no helper).
- The input building the planner and mission wrappers do today lives in the brain's methods after phase 3.
- `ActionEnvelope.act` is unwrapped in the brain.
- The repeated docstring paragraph on the input models goes; the rule is stated once, where `StructuredLLMChain` is used or in `docs/`.
- Tests that mock a wrapper mock the chain attribute instead; `laife.llm.scripted_chat` needs no change, since it answers by output schema.

## Done when

- No class in `src/laife` only wraps a `StructuredLLMChain`.
- `make check` passes; `make headless` gives the same positions as on `main`.
