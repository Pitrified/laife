---
status: planned
---

# Phase 3 - Scripted chat model

## Overview

A fake chat model that answers each structured-output call by schema, from a fixed script per player.
Context: [`00_start.md`](00_start.md) Q1, Q2, Q3.

## Plan

- In laife, under `src/laife/llm/scripted/`:
  - `ScriptedChatModel(BaseChatModel)`, shaped like llm-core's `FakeChatModel`:
    `with_structured_output(schema)` returns a `RunnableLambda` that asks the policy for an instance of `schema`.
  - `ScriptedChatConfig(ChatConfig)`, with `model="scripted"` and `model_provider="scripted"`, whose `create_chat_model()` returns it.
    The `llm_call` log events record the model name, so a scripted run is visible as one in the log and the TUI.
- The policy answers by output model:
  - `ActionEnvelope`: the next action from the player's script, cycling.
  - `WorldJudgeResult`: success, with a fixed feedback string.
  - `MissionGeneratorResult`, `PlayerPlannerResult`, `PlayerReplyOutput`: fixed values.
  - Any other schema: a named error, so a new chain shows up as a failure rather than as a silent default.
- Which player is asking: the chains get the rendered prompt, not the player.
  So `Player.__init__` and `WorldRunner.__init__` each take a `chat_config: ChatConfig | None = None`, `None` meaning `chat.default`,
  and each player gets a `ScriptedChatConfig` carrying its own script; the runner gets one for its three judges, which need no player identity.
  Reading the player name out of the rendered prompt was the alternative, and is the prompt parsing Q2 ruled out.
  Decided with the user 2026-11-12. The same argument lets the live game give the world and the players different models later, such as a stronger judge; not done here.
- The default script walks every branch of the turn `match`: plan, move, build, craft, interact with the other player, complete.

## Done when

- Unit tests: each schema gets a valid instance; the cycle wraps; an unknown schema raises.
- `make check` passes.
