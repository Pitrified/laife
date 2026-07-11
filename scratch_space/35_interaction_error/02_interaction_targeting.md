---
status: in progress
---

# Phase 2 - interaction targeting

## Overview

The model addressed `'Big ol Farm'` (a building) with `ActionInteract`, whose
`target_name` is documented as "Name of the player to address". Investigate why
and decide the direction: prompt steering, target validation, or a new
capability. Depends on [`01_survive_wres_error.md`](01_survive_wres_error.md)
landing first, so live experiments do not crash the game.
Context: [`00_start.md`](00_start.md).

## What the code already tells us

Read during planning (2026-07-11):

- The observation rendering (`world_map_observation.py:49`) labels every
  entity with its type: `- Building "Big ol Farm" is to the ...` next to
  `- Player "p1" is to the ...`. The model could see the target was a
  building and messaged it anyway - the mission was "gather crops", and
  `ActionInteract` is the only action that takes a `target_name` at all.
  So the leading hypothesis is **capability gap** (a reasonable intent with
  no action to express it), not name confusion.
- Nothing validates `target_name`: the request goes to the world, which
  answers `WResError` only after the fact.

## Goals

1. Evidence on how often and why non-player targets get picked
   (captured logs plus live runs with phase 1 in place).
2. A direction decision recorded here - steer, validate, or extend - with
   the evidence that drove it.
3. The cheap mitigations implemented regardless of direction (they are
   compatible with all three outcomes).

## Plan

Investigation:

- Sweep existing `cache/game_*.jsonl` logs for `action_type=ActionInteract`
  rows and classify targets (player vs building vs terrain vs hallucinated).
- Run a few live sessions (post phase 1) and watch how the brain reacts to
  the error line now present in history: does it self-correct next turn,
  or loop on the same building?

Cheap mitigations (do these in this phase, they help all directions):

- Tighten the `ActionInteract.target_name` field description to say the
  target must be a *player* and that buildings cannot be addressed.
- List the valid interaction targets (nearby player names) explicitly in the
  action-picker prompt, next to the action inventory.

Decision fork - pick with the evidence, record the choice here:

- **Steer**: if mitigations alone drop the miss rate to noise, stop there.
- **Validate**: reject a non-player `target_name` before sending the world
  request, feeding a targeted "you can only message players; nearby players
  are: ..." line into history (faster feedback than the world round trip).
- **Extend**: if runs keep showing sensible building-directed intents
  ("gather crops"), scope a building-interaction action as its own follow-up
  phase (NN_building_interaction.md) rather than growing this one.

## Out of scope

- Implementing building interaction mechanics (crops, inventories) - if the
  fork lands on extend, that becomes its own phase.

## Progress (2026-07-11)

Done up to the point where a live game is needed:

- Both cheap mitigations landed:
  - `ActionInteract.target_name` description (and the action docstring) now
    say the target must be a player and that buildings/terrain cannot be
    addressed - this reaches the model through the structured-output schema.
  - New `WorldMapObservation.nearby_players_to_prompt()` lists nearby players
    (nearest first, quoted names, or an explicit "None - no other players are
    within range."); `ActionPickerInput` gained a `nearby_players` field,
    `PlayerBrain.think` fills it from the observation, and the new
    `prompts/player_brain/v3.jinja` renders it as a
    "Nearby players (valid interaction targets)" section with a closing
    guidance line. `version: auto` resolves to v3 (smoke-checked, chain
    validation passes).
  - 2 new tests for the listing (empty case, filter+sort); brain tests
    updated for the new variable. Suite green: 228 passed, ruff and pyright
    clean.
- Classification sweep: **blocked, no data** - `cache/` holds no `.jsonl`
  logs on this box (past live-run logs were not kept). The sweep needs logs
  from future live sessions.

Remaining, needs a live game:

- Run live sessions and watch how the brain reacts to the error line in
  history (phase 1) and to the new target listing: does it self-correct,
  or loop on the same building?
- Classify interact targets from those fresh logs.
- Record the steer / validate / extend fork decision here with that evidence.

## Done when

- The classification sweep and live-run observations are written up here.
- The two cheap mitigations are implemented and verified in a live run.
- The fork decision is recorded with evidence (and, if extend, the follow-up
  phase is drafted in `tracking.md`).
- Project verification suite passes.
