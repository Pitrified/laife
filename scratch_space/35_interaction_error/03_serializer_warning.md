---
status: draft
---

# Phase 3 - serializer warning

## Overview

During the same captured run, pydantic warned while serializing:
`Expected 'none' - serialized value may not be as expected [field_name='parsed',
input_value=ActionEnvelope(...)]`. The `parsed` field name points at the
langchain structured-output envelope (include_raw style), not at our own models.
Pin down where the serialization happens and whether a schema on our side is
looser than it should be. Context: [`00_start.md`](00_start.md).

## Goals

1. Identify the exact serialization call that triggers the warning and whether
   it originates in `StructuredLLMChain` usage or inside langchain.
2. Remove the warning by tightening the schema/usage, or record it as upstream
   noise with a targeted suppression and a pointer to the upstream issue.

## Plan

- Reproduce with a minimal structured call (the action picker path) and
  `warnings.simplefilter("error")` to get a stack trace at the warning site.
- Inspect the model the trace points at; check whether `parsed` is typed `None`
  somewhere it can legitimately hold the output model.
- Fix on our side if the type is ours; otherwise suppress narrowly with a
  comment, as in the `34_runtime_warnings` convention.

## Out of scope

- Any langchain version bump (that lives in
  [`34_runtime_warnings/02_pydantic_v1_warning.md`](../34_runtime_warnings/02_pydantic_v1_warning.md)
  if it comes up).

## Done when

- The warning's origin is documented here and it no longer fires on a real run,
  or the suppression decision is recorded and applied.
- Project verification suite passes.
