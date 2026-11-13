---
status: done
---

# Phase 2 - OpenAI only and install weight

## Overview

Drop the provider configs nothing selects, and the dependencies nothing uses. Context: [`00_start.md`](00_start.md).

## Plan

### Params

- `ChatParams` and `EmbeddingsParams` keep only the OpenAI config; Azure, HuggingFace and Ollama go.
  The embeddings and vector store params stay, OpenAI and Chroma, for the planned vector store work.
- `default` stays as the name: `Player`, `WorldRunner`, `setup_world` and the search params read it, so no caller changes.
- The five tests that build an `OllamaChatConfig` as a placeholder use `ScriptedChatConfig` from `laife.llm.scripted_chat`.
  Not `ChatOpenAIConfig`: building the chain creates the model, and `ChatOpenAI` needs `OPENAI_API_KEY` there, which a clean checkout lacks.

### Dependencies

Decided with the user, 2026-11-13.

- `llm-core[openai,chroma]` instead of `[all]`, in `pyproject.toml` and in the `dev-llm-core` target of the `Makefile`.
- Drop `transformers` and `langgraph`: nothing in `src`, `tests` or `game` imports them.
- Drop `pysqlite3-binary`: it worked around an old chroma bug needing a newer sqlite. The interpreter's sqlite is 3.53.1, above chroma's 3.35 minimum, and no code swaps the module in. Kept out only if the check below passes.
- `ipywidgets` stays: notebooks may use it through progress bars.
- Relock, `make sync`; read `uv tree --invert --package torch` and record what, if anything, still pulls torch.

### Dead code and mentions

- Delete `src/laife/embed/` and `scratch_space/embed_/sample.ipynb` (Q4).
- Remove `docs/library/embed.md`, its `mkdocs.yml` nav entry, and the `embed` mentions in `docs/library/README.md`.
- `nokeys.env`: remove the two `AZURE_OPENAI_*` keys. `~/cred/laife/.env` is the user's file and is not touched.
- `.github/copilot-instructions.md`, "LLM provider abstraction": the provider list becomes OpenAI.
- Four other `scratch_space/` files import Ollama or HuggingFace. Pyright checks only `src` and `tests`; they are left to break, as the embed notebook did.

The lock change is reviewed by the user before the commit.

## Done when

- `uv.lock` has no torch, or the remaining path to it is recorded here with a reason.
- Chroma works without `pysqlite3`: a scratch script creates an in-memory `chromadb` client, adds a document with a fake embedding and queries it back. If it fails, `pysqlite3-binary` stays and the failure is recorded here.
- `make check` passes, including the strict docs build; `make headless` gives the same positions as on `main`.

## Outcome

- `ChatParams` and `EmbeddingsParams` hold only the OpenAI config; `default` kept. The five tests use `ScriptedChatConfig`.
- `pyproject.toml`: `llm-core[openai,chroma]`; `transformers`, `langgraph` and `pysqlite3-binary` removed; `dev-llm-core` installs the same extras.
- The lock has no torch, no CUDA wheels, no sentence-transformers, whisper or Ollama client; `.venv` went from several GB to under 1 GB.
- `langgraph` stays in the lock as a transitive dependency: llm-core's `langchain` 1.x requires it. Only the direct pin went.
- Chroma without `pysqlite3`: an in-memory client added two documents with fake embeddings and returned the right one on query, on sqlite 3.53.1 and chromadb 1.5.9. `pysqlite3-binary` stays out.
- `laife.embed`, its notebook and docs page removed; Azure keys out of `nokeys.env`; the docs and the instructions say OpenAI only.
- `make check` passes with one test fewer: `tests/test_models_build.py` has a case per laife pydantic model, and `SentenceTransformersEmbeddings` was one. `make headless` with the default seed ends with both players at the same positions as before.
- Lock review: removals only, 44 packages, no version changed. `setuptools` went with torch, its only dependent here; pygame imports, opens a dummy display and loads a font without it.
