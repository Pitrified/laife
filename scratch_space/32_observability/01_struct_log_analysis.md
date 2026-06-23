---
status: planned
---

# Phase 1 - struct log analysis

## Overview

Catalogue what the structured sink already emits so the UI knows what to filter
and group on. The JSON-lines sink already exists (`configure_logging()` in
`src/laife/meta/logger.py`); this phase is inventory and gap-finding, not new
plumbing. Context: [`00-start.md`](00-start.md).

## Goals

1. A complete catalogue of event types and their per-event payload fields.
2. The natural filter axes the UI will offer.
3. A decision on the missing fields needed to reconstruct one interaction.

## Plan

- Inventory event types from `src/laife/meta/log_events.py`: `action`,
  `world_response`, `mission_transition`, `llm_call`, `llm_result`,
  `world_request`. Note every record also carries loguru's `time`, `level`,
  `message`, and that `world_request` is `DEBUG` while the rest are `INFO`.
- Map per-event payload (the fields passed to `slog.bind(...)`):
  - `action`: `player`, `action`
  - `world_response`: `player`, `kind` (build/craft/...), `status`
  - `mission_transition`: `player`, `to_status`
  - `llm_call`: `model`, `elapsed`
  - `world_request`: `kind` (request class name)
- Identify filter axes: **player**, **event type**, **status**, **time**. Note
  that `world_request`/`llm_call` lack `player`.
- Decide on correlation: there is no id tying `llm_call` -> `action` ->
  `world_request` -> `world_response`, and no tick/turn number. Decide whether
  to add a `request_id` / `turn` field at the bind sites.
- Check for PII/secret leakage in serialized records before any UI renders them.

## Out of scope

- Changing the bind sites / adding new fields (decision only here; the edit, if
  agreed, lands when the consuming UI needs it).
- Building any renderer (phase 2).

## Done when

- The catalogue above is recorded (in this file or a short doc) and confirmed
  against the live `.jsonl`.
- A go/no-go decision exists on adding correlation id + turn number.
