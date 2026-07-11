---
status: draft
---

# Phase 2 - interaction targeting

## Overview

The model addressed `'Big ol Farm'` (a building) with `ActionInteract`, whose
`target_name` is documented as "Name of the player to address". Investigate why
the pick happened and decide whether the fix is prompt steering, target
validation, or a new capability (interacting with buildings is a sensible thing
to want - "gather crops" was a reasonable intent with no action to express it).
Depends on [`01_survive_wres_error.md`](01_survive_wres_error.md) so experiments
do not crash the game. Context: [`00_start.md`](00_start.md).

## Goals

1. Understand the pick: what the observation prompt lists as names, and whether
   player and building names are distinguishable to the model.
2. A decision, recorded here, on the direction:
   steer (prompt), validate (reject early with useful feedback), or extend
   (a building-interaction action). Implementation of the chosen direction.

## Plan

- Read the observation/prompt rendering (`world_map_observation`, action picker
  prompt) and reproduce the confusion against a live backend or captured logs.
- Cheap mitigations to evaluate while investigating: name the target field more
  strictly, list valid interaction targets in the prompt, or validate
  `target_name` against known players before sending the request.
- If the investigation says building interaction is the real feature, scope it
  as its own follow-up phase rather than growing this one.

## Out of scope

- Implementing full building interaction mechanics (crops, inventories) - that
  would be its own effort.

## Done when

- The direction decision is recorded with evidence, and the chosen mitigation is
  implemented and observable in a real run.
- Project verification suite passes.
