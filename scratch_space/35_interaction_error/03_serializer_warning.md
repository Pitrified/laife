---
status: planned
---

# Phase 3 - serializer warning

## Overview

During the captured run, pydantic warned while serializing:
`Expected 'none' - serialized value may not be as expected [field_name='parsed',
input_value=ActionEnvelope(...)]`. Independent of phases 1-2; can run any time.
Context: [`00_start.md`](00_start.md).

## What the code already tells us

Read during planning (2026-07-11):

- No `parsed` field exists anywhere in laife. The structured path is
  `llm_core.chains.structured_chain.StructuredLLMChain`, which builds
  `prompt | model.with_structured_output(output_model)`
  (`structured_chain.py:91` in the installed package).
- The `parsed` field name belongs to langchain's `with_structured_output`
  internals (its raw+parsed envelope), so the warning fires inside
  langchain/langchain-openai when something serializes that envelope
  (likely callback/tracing or the provider response dump), with our
  `ActionEnvelope` as the payload.
- `llm-core` is our own package, pinned as a git dependency at tag `v0.2.2`
  (`pyproject.toml:11`). If the fix belongs in the chain construction,
  it is a cross-repo change: patch `Pitrified/llm-core`, tag, bump the pin.

## Goals

1. A stack trace pinning the exact serialization site
   (ours / llm-core / langchain).
2. The warning no longer fires on a real run - via a fix at the right layer,
   or a narrow suppression naming the upstream issue.

## Plan

- Reproduce minimally: drive one `ActionPicker.ainvoke` against the live
  backend with `warnings.filterwarnings("error", message=".*Expected .none.*")`
  (or `PYTHONWARNINGS`) to turn the warning into a traceback.
- Read the frame the trace points at:
  - if it is llm-core chain construction (e.g. a `method=` or `include_raw=`
    choice on `with_structured_output`), fix there, tag a release, bump the
    pin here;
  - if it is pure langchain internals, check upstream issues for the warning
    signature; suppress narrowly at `configure_logging` with a comment naming
    the issue and the removal condition (mirror the convention in
    [`34_runtime_warnings`](../34_runtime_warnings/00_start.md)).
- Verify: a live `make run` session (or the minimal repro) no longer prints
  the warning; note in this file which layer it was.

## Out of scope

- Any langchain version bump (that lives in
  [`34_runtime_warnings/02_pydantic_v1_warning.md`](../34_runtime_warnings/02_pydantic_v1_warning.md)
  if it comes up).
- llm-core changes beyond the one chain-construction fix, if that is the site.

## Done when

- The warning's origin layer is documented here and it no longer fires on a
  real run, or the suppression decision is recorded and applied.
- Project verification suite passes.
