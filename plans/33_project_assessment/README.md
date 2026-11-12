---
status: draft
---

# Project assessment - 2026-07-06

An outside read of the whole repo: architecture, tests, tooling, docs, and the gap between `plan.md`/`README.md` ideas and what's actually implemented.
Written from static reading of the code plus git history; see the caveat on verification at the bottom before trusting the "all green" claims.

## What this project is

lAIfe is an LLM-driven life-simulation game: `Player` agents perceive a Pygame world through an async message-passing layer, call an LLM "brain" to pick an action, and the world validates the action (partly deterministically, partly via an LLM "judge") before applying it.
Solo project, Python 3.14, `uv`-managed, 50 commits from 2026-02-25 to 2026-06-23, roughly 3400 lines of `src/laife` against roughly 3100 lines of tests.

## Good

- **Rendering/simulation split is real, not aspirational.** `WorldRunner` (`src/laife/entities/world_runner.py`) has zero pygame imports; `WorldRenderer` (`src/laife/rendering/world_renderer.py`) holds a read-only reference to the runner and owns all pygame state. This is claimed in `.github/copilot-instructions.md` and it actually holds up when you read the imports.
- **Action/response modeling is clean.** `Actions` and `WRes` are discriminated unions of pydantic models, dispatched with `match`/`case` in `Player.play()` and `WorldRunner.handle_player_input()`. Adding a new action type touches a small, obvious set of places.
- **Mission/sub-mission design is well thought through.** `Mission` (`src/laife/llm/mission.py`) supports nesting with parent pointers, `active_focus()` walking to the deepest active step, `advance()` propagating completion upward, and failure counting that trips a `FAILED` status after `MAX_MISSION_FAILURES`. It's genuinely recursive and matches the nested-mission idea in `README.md`, not just a flat todo list wearing a tree-shaped API.
- **Test coverage is substantial and the tests are real.** Roughly 1 line of test per 1.1 lines of source, and spot-checking (`tests/entities/test_mission_step_runner.py`) shows targeted unit tests with meaningful assertions, not smoke tests. Player is tested via `object.__new__(Player)` plus manual attribute injection to avoid needing a live LLM/world, which is a reasonable way to unit-test a class with a heavy constructor.
- **Tooling discipline is unusually high for a solo hobby repo.** Ruff runs `select = ["ALL"]` with a short, justified ignore list; pyright is scoped to `src` and `tests`; there's a `Makefile` wrapping every common command; docs are built with MkDocs and published on every push to `main`, with a `docs_maintenance.md` checklist (dead-link grep, library-page-per-package diff, strict `mkdocs build`) that most personal projects never bother writing.
- **`plan.md` is kept honest.** Items are struck through as `(done)` and match what's actually in the code (checked terrain, typed `WRes`, inventory, mission lifecycle, interaction, structured logger, generic `_world_request` helper - all present). The gap between plan and reality is small, which is a good sign for whether to trust the rest of the docs.
- **Self-awareness of duplication already exists.** The README todo list includes "the action picker and world judge are quite similar, try to create a superclass" - the project already knows about the issue flagged below; it just hasn't been paid down yet.

## Bad / risks

- **Five near-identical LLM-chain wrapper classes.** `PlayerBrain`, `PlayerPlanner`, `PlayerReplier`, `MissionGenerator`, and `WorldActionJudge` (plus `ActionPicker`) all follow the exact same shape: a `Config(BaseModel)` holding `chat_config` + `prompt_loader_config`, an `Input(BaseModelKwargs)`, a `@dataclass` with `__post_init__` building a `StructuredLLMChain`, and `invoke`/`ainvoke` pass-throughs. This was two classes when the "superclass" TODO was written; it's six now, so the refactor is getting more expensive to defer, not less. A `BaseLLMChain[InputT, OutputT]` base (config + chain construction + invoke/ainvoke) would cut this to one implementation per subclass: the input model and the prompt name.
- **`WReq`/`WRec*` boilerplate in `world_channel.py`.** Every request subclass (`WRecBuild`, `WRecCraft`, `WRecMove`, ...) hand-writes `__init__(self, ..., *args, **kwargs)` forwarding to `super().__init__(*args, **kwargs)`, each with a `# noqa: ANN002, ANN003`. They're plain classes instead of pydantic models because they carry an `asyncio.Queue` (a real constraint, pydantic would need `arbitrary_types_allowed`), but `@dataclass(kw_only=True)` would remove the manual `__init__`/`*args`/`**kwargs` boilerplate while keeping that constraint satisfied.
- **Two parallel logging paths, called from the same call sites.** `alg.log(...)` (console, dedup-printing `Alog` singleton in `src/laife/ui/alog.py`) and `slog.bind(...).info(...)` (structured JSONL via loguru, `src/laife/meta/logger.py`) are both invoked for the same event in `Player` and `WorldRunner` (e.g. `build()`, `craft()`, `_update_mission_from_response()`). Keeping a human console channel and a machine-readable trace separate is reasonable; having every call site manually keep both in sync with overlapping content is not - one will eventually drift and only one of the two will show the real story.
- **Judge-then-collision-check ordering wastes LLM calls.** `WorldRunner.judge_and_build()` invokes the (network-latency, token-cost) LLM judge first, and only checks the free, deterministic spatial collision afterward via `add_building()`. A build request that's going to be rejected on a collision (e.g. someone re-building on an already-occupied tile) still pays for a full LLM round trip before being told no. Swapping the order - deterministic checks first, judge only for requests that pass them - is a pure win with no behavior change for the success path.
- **Singleton pattern with no reset hook.** `LaifeParams` and `Alog` both use the same `Singleton` metaclass (`src/laife/meta/singleton.py`), which has no way to clear `_instances`. Several test files reference `Singleton` directly, which suggests tests are reaching into `_instances` to reset state between runs rather than the class being designed for that. A `reset()` classmethod (or dependency injection instead of a metaclass singleton) would make that explicit instead of implicit.
- **Exact Python pin (`requires-python = "==3.14.*"`).** Python 3.14 is very new and `pygame` doesn't yet ship a prebuilt wheel for it on this platform - `uv run` tries to build pygame from source and needs SDL2/freetype dev headers (`CONTRIBUTING.md` documents this correctly). That's a real fragility: every fresh machine setup is one apt-get away from a build failure, and the exact pin means there's no `>=3.13,<3.15` fallback if a 3.14 wheel is late. Worth confirming there's a specific 3.14-only language feature in use before keeping the pin this tight.
- **Config/params layering may be ahead of its actual use.** `LaifeParams` (singleton) owns `LaifePaths` and `LLMServicesParams`, which in turn wrap `llm_core`'s `ChatConfig`/`EmbeddingsConfig` across Ollama/OpenAI/Azure/HuggingFace subclasses. That's legitimate if providers are actually swapped at runtime; worth a quick check of whether more than one provider is exercised today, since if it's always OpenAI in practice, some of this layering is speculative flexibility rather than paid-for flexibility.

## Missing (against the project's own plan)

- **Vector DB isn't wired into gameplay yet.** `ChromaConfig` exists and is unit-tested (`tests/llm_services/vectorstores/test_chroma_config.py`), but `plan.md` item 6 ("seed starter utensils into the vector store, give the brain a retrieval step") isn't implemented - `player_brain.py` never queries a vector store before picking an action.
- **Interaction memory (plan.md item 11) not started.** `Player.receive_message()` generates a reply via `PlayerReplier` but doesn't persist the incoming message anywhere; there's no `interactions: list[Interaction]` field yet, so a player has no memory of having been talked to.
- **Observability is still a draft.** `scratch_space/32_observability/README.md` is marked `status: draft` and recommends a Textual TUI tailing the JSONL log, but nothing consumes the structured log yet beyond the raw file - if you wanted to actually debug a multi-agent run today, you'd be grepping `cache/game_*.jsonl` by hand.
- **Terrain/building tiling ("prettier background", per `README.md`'s feature checklist) is unchecked** - rendering currently fills flat colors per `_TERRAIN_COLORS`, not tiled sprites.

## Verification

SDL2 is now installed on this box and `~/cred/laife/.env` (previously empty) has been seeded with the placeholder values from `nokeys.env`, so the full suite could actually be run instead of read about:

- `make sync`: clean, `pygame` builds and imports (`pygame 2.6.1 (SDL 2.32.10, Python 3.14.4)`).
- `make test`: **181 passed**, 0 failed, in 8.63s. Three warnings, none from `laife` code: a `chromadb` `asyncio.iscoroutinefunction` deprecation, a `langchain_core` warning that pydantic v1 compat isn't supported on Python 3.14+, and pygame's AVX2-not-compiled-in notice.
- `make lint` (ruff, `select = ["ALL"]`): **2 errors, both outside the package** - unsorted import blocks (`I001`) in `scratch_space/12_action_structure/discriminator_test.ipynb` and `scratch_space/entities_/utensil_.py`. Both are auto-fixable with `ruff check . --fix`. `src/` and `tests/` are clean.
- `make typecheck` (pyright, scoped to `src` and `tests`): **0 errors, 0 warnings, 0 informations.**

So the earlier concern about the exact `==3.14.*` pin being fragile was confirmed in one respect (the `langchain_core` pydantic-v1 warning is a direct symptom of running on 3.14) but not a blocker: everything that matters (`src/`, `tests/`) is green. The only outstanding lint noise is in exploratory scratch files, which the repo's own ruff config already treats more leniently than the package proper (just not for import sorting).

## Bottom line

This is a well-organized, honestly-tracked hobby project with better-than-typical tooling and test discipline.
The main technical debt is self-inflicted duplication across the LLM-wrapper classes and the world-request classes - both already half-acknowledged in the project's own notes - plus one clear performance/cost bug (judge-before-collision-check) that's a small, low-risk fix.
Nothing here looks like it needs a rewrite; the plan.md backlog is the right next set of steps, in roughly the order it's already written.
