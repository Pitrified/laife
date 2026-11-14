---
status: discarded
---

# Phase 3 - pygame avx2 warning

Discarded 2026-11-14: pygame left the repo in `41_renderer_choice` phase 5. pygame is no longer a dependency, so its AVX2 notice cannot appear.

## Overview

The prebuilt pygame wheel warns at import that the system is AVX2 capable
but the wheel was not built with AVX2 support. Cosmetic; lowest priority.
Context: [`00_start.md`](00_start.md).

## Goals

1. `make run` startup no longer prints the AVX2 RuntimeWarning
   (fixed or deliberately suppressed).

## Plan

- Evaluate `pygame-ce` as a drop-in replacement (it ships AVX2 wheels);
  check our pygame API surface (`world_renderer.py`, sprites) against it.
- If not worth the swap, suppress the specific RuntimeWarning at the game
  entrypoint with a comment, and note the decision here.

## Out of scope

- Building pygame from source.
- Any rendering performance work beyond removing the warning.

## Done when

- The warning is gone from a real `make run` startup, or the suppression
  decision is recorded and applied.
- Project verification suite passes.
