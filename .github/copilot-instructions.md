# lAIfe - Copilot Instructions

## Project overview

lAIfe is an LLM-driven life-simulation game built on Pygame + asyncio. Players are autonomous AI agents that perceive the world, plan missions, and issue actions; the game engine validates and executes those actions. Python 3.14, managed with **uv**.

The LLM plumbing (provider configs, structured chains, prompt loading, vector stores) lives in the sibling package [`llm-core`](https://github.com/Pitrified/llm-core), pinned by git tag in `pyproject.toml`.
Before writing a utility of that kind here, look in `llm_core` first; if it is general, it belongs there.

## How to write

Technical prose: dry, concrete, and short without leaving anything out. That target is easier to
recognise by its two failure modes. On one side, padding that makes a page longer without making
it say more. On the other, cutting the detail that was the reason to write the sentence at all.
Aim between them.

Behind most of the habits below is one failure, worth naming because it explains the rest.
The mannered writer reaches for the unusual word to show what he is, rather than to show the reader what he means.
Prose is a window onto the subject, and the mannered kind is a window with the writer's face reflected in it.
Pinker calls the alternative classic style: the writer has seen something and is pointing at it.
An agent writing here inherits the same tic from its training data, so the rule is the same for both of us:
the word that carries the meaning, not the word that carries the writer.

The specific habits to avoid:

- **No hype.** Adjectives and adverbs that carry tone but no information: seamless, robust,
  powerful, elegantly, simply, blazing. Cut them, or replace them with the concrete fact, subject
  to the next rule.
- **No volatile numbers.** A number that changes with the next run is a measurement with a date
  on it. Leave it out. An order of magnitude is fine where the size is the point. Ports, versions
  and retention windows hold still and stay.
- **A count of what is in the repository is a volatile number.** How many actions the union has,
  how many prompts exist, how many tests pass: each changes with an ordinary edit, the file being
  counted is already the answer, and the count is the copy that rots.
- **Nothing a reader could get mechanically.** A table that mirrors a directory, a list that is `ls`
  of a folder. Say where the answer is and let them look. Prose is for the rule, the reason, the
  trap and the pointer.
- **No padding.** One idea stated once. Do not restate a point in three framings, and do not open a
  paragraph by announcing what it is about to say.
- **No fake drama.** The "it is not X, it is Y" reveal. The countdown that rules out two things
  before naming the third. The one-sentence paragraph deployed as a punchline. The "X is the Y of
  Z" metaphor.
- **No thesaurus reach.** delve, leverage, unleash, realm, landscape, ever-evolving, meticulous,
  underscore, boast, harness, tapestry, testament, quietly, bites, load-bearing. A sample, not an
  exhaustive blacklist. Ordinary words instead.
- **Plain copulas.** "is" and "are", not "serves as a", "stands as", "represents".
- **No closing summary** repeating what the page just said, and no motivational sign-off.
- **No emoji**, and no decorative headers. Headers are plain labels, no parentheticals.
- **No confident filler where a fact is missing.** If a value is unknown, say it is unknown and
  say who would know.
- **Mechanical.** No em dashes (`--`, `---`, or Unicode). Use a hyphen or rewrite the sentence. Do
  not wrap markdown to a fixed column; break lines on logical boundaries instead, such as after a
  period or between clauses.

The list is the recurring failures, not the definition.
`.claude/skills/deslopify/` scans a file for them; its `house_rules` category is part of `make check`, the rest is run by hand and triaged.

### Comments and docstrings

A docstring says what the name does, its units, and the trap a reader would fall into that the code does not show. Nothing else.

- **No history.** Not what a value was before, when it changed, or which run found it. Git holds that. A past mistake that is easy to make again is written as the present rule.
- **No plan citations.** Nothing outside `plans/` points at a plan folder or at `scratch_space/`; `plans/` is a diary. A reason a docstring needs goes into the docstring or into a page under `docs/`. `make plans` checks the plan-folder half.
- **When a value changes, rewrite the paragraph to the present** rather than adding a "was" sentence beside the old one.
- **No counts and no claims a search answers** ("nothing else calls this"). They rot.

## Planning

Plans are written to keep the reasoning from being re-derived, not to close the question.
Anything in them can be reopened: a decision, an answered question, a phase, the shape of the whole thing.
Reopening on new evidence is the plan working, not the plan failing.
Record what changed and leave the previous answer visible rather than editing it away.

Write each point at the strength it actually has.
"for now", "until the spike reports", "unless X changes" are accurate about most choices and cost nothing to write.
Reserve "never", "must" and "hard requirement" for the few things that really are fixed.
A line written as an absolute gets read a month later as a deal breaker, and then something obvious does not get tried.

Weight remarks by how they were made.
An offhand comment is a signal, not an instruction.
When one would become a constraint, either mark it provisional in the plan or ask before promoting it.

Planning is cooperative: the functional and technical details are worked out with the user, in rounds, not decided alone.
`.claude/skills/grill-me/` is the interview for an idea too vague to plan against.

### Where plans live

- `plan.md` is the backlog: future work, unnumbered, one place. An item stays there until it is picked.
- Picking an item creates `plans/NN_name/`, numbered in creation order, in the `tracked-development` layout: `00_start.md` with frontmatter, `tracking.md`, one file per phase.
- `python3 scripts/plans.py list` shows the folders by status and priority; `make plans` checks them.
- `scratch_space/` holds throwaway notebooks and scripts, never plans.

## How to build

- **Small primitives over complete APIs.** A function that answers one question well composes; a method for every phrasing of the question does not.
- **No config knobs without a case.** A parameter with one caller and one value is a constant.
- **Build the case in front of you,** not the general one it might become.
- **Errors say what is wrong and with which input.** Raise a named exception (`UnknownEnvLocationError`), not a bare `ValueError`.

## Running the engine

Unit tests passing is not evidence that the game works. While planning and while implementing, the evidence is the engine running: a game run, its structured log in `cache/game_*.jsonl`, and what `make tui` shows of it.

What exists today and its limits:

- `make run` opens the pygame window and calls the configured LLM provider for every player turn. It needs a display and real credentials, so it costs money and is run by or with the user.
- `make tui` reads the newest structured log; `SimControl` pauses and steps the loop.
- There is no headless run with a scripted LLM yet. It is a `plan.md` item, and until it exists a change to game behaviour is not verified by an agent alone: say so rather than calling it done.

## Unattended work

Only small implementation changes run without the user watching. A phase qualifies when:

- its file is `planned` and its folder has no open `NEW_ANS`;
- it runs on a feature branch, with no merge to `main`;
- it adds no dependency;
- a prompt version or a data model changes only where the phase plan names that change;
- `make check` passes before every commit.

Anything outside that stops and asks. Decisions taken along the way go into the folder's `00_start.md` as a batch marked as decided by the agent, for the user to review.

## The mechanical checks

`make check` is lint, formatting, types, the plan folders, tests and the strict docs build, in one target. Run it, read it, and fix what it says before calling a piece of work done. `make` on its own lists every target.

The pre-commit hooks run on every commit once installed with `make hooks`, once per clone: ruff check and format, pyright, notebook outputs stripped, no secrets, file hygiene, the plan folders and the house writing rules. Tests are not in the hook; `make check` covers them. Never skip the hooks with `--no-verify`; fix the finding.

- **Run `make check` before the commit, not after.** A commit made first and checked second is a commit somebody else finds.
- **A skipped test is not a passed test.** Read the count. Fewer tests than last time means something stopped being collected.
- **Always run project code through `make`, or `uv run --no-sync`.** A bare `uv run` re-syncs the environment from `uv.lock` first, which reverts a local editable install of llm-core (`make dev-llm-core`). `make undev` is the deliberate way back.
- **Hook versions follow `uv.lock`.** ruff, pyright, nbstripout and detect-secrets are pinned exactly in `pyproject.toml` to their hook `rev`; move both together. `scripts/check_tool_pins.py`, the `tool-pins` hook, fails when they differ; python-project-template's `docs/guides/pre_commit.md`, "Tool versions", has the procedure.
- **A gate has to stay fast enough to be run.** A slow gate gets skipped, and a skipped gate is a wish. One command, a failure that names the file and what to do, and shown failing once before it counts.
- The docs are published to GitHub Pages by `.github/workflows/docs.yml`, which runs `mkdocs build --strict`. `make docs-check` is the same build, so a docs break is caught before it reaches CI.

## Which box

Two machines, and they differ in ways that matter. Establish which one you are on rather than assuming.

```python
import platform

platform.node().lower().startswith("pmn-14g4")  # g4, else g7
```

- **g7** is the dev box: unattended agent sessions, sometimes used with a UI. Agent sessions have no `DISPLAY`. uv's managed Python 3.14 is the interpreter, because the system one lacks the headers pygame needs to build (pygame 2.6 has no 3.14 wheel).
- **g4** is the laptop a person sits at.

## Architecture layers

| Layer         | Path                                    | Role                                                                                                                                              |
| ------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Game entry    | `game/main.py`                          | Pygame loop + asyncio bridge; spawns `WorldRunner.simulate()` and `Player.play()` as concurrent tasks, then drives the Pygame event loop          |
| Rendering     | `src/laife/rendering/world_renderer.py` | `WorldRenderer` reads `WorldRunner` state and converts it into Pygame sprites/window; display dependency is isolated here, `WorldRunner` has none |
| Simulation    | `src/laife/entities/world_runner.py`    | Authoritative state, processes `WReq` messages                                                                                                    |
| Entities      | `src/laife/entities/`                   | `Player`, `Building`, `Utensil`, `Terrain`                                                                                                        |
| AI brain      | `src/laife/llm/player_brain.py`         | `PlayerBrain.think()` → `BaseAction`                                                                                                              |
| Actions       | `src/laife/entities/action.py`          | The `Actions` discriminated union of `BaseAction` subclasses                                                                                      |
| Missions      | `src/laife/llm/mission.py`              | `Mission` owns `MissionHistory`; supports nested sub-missions                                                                                     |
| LLM services  | `src/laife/params/llm_services/`        | Which llm-core chat, embeddings and vector store configs this game uses                                                                           |
| Config/params | `src/laife/params/`                     | Singleton `LaifeParams`; `LaifePaths` for all filesystem refs                                                                                     |
| Observability | `src/laife/observability/`              | The Textual TUI over the structured log                                                                                                           |

## Key patterns

**World <-> Player communication via async queues**
Players put `WReq` subclasses (e.g., `WRecBuild`, `WRecObserve`) into `WorldRunner.input_queue`. Each request carries its own `response_queue`; the runner puts a `WRes` back there. This decouples the simulation loop from any display dependency.

**LLM provider abstraction via llm-core config subclasses**
Chat models, embeddings and vector stores are built from llm-core config objects (`ChatConfig.create_chat_model()`, `EmbeddingsConfig.create_embeddings()`, `VectorStoreConfig`), with provider subclasses for Ollama, OpenAI, Azure OpenAI and HuggingFace. Never instantiate the LangChain objects directly.

**Structured chains**
Every LLM call that returns a model goes through llm-core's `StructuredLLMChain[InputT, OutputT]`.

**Versioned Jinja prompts**
Prompts live in `src/laife/prompts/<name>/vN.jinja`, loaded by llm-core's `PromptLoader`; `version="auto"` picks the highest version. Add a new prompt version by creating `vN+1.jinja`; never edit an existing version file.

**`Vectorable` protocol for entity serialization**
Entities that round-trip through a vector store implement llm-core's `Vectorable`: `to_document() → Document` and `from_document(doc) → Self`, writing `entity_type` into `doc.metadata`.

**`BaseModelKwargs`**
Config classes extend `BaseModelKwargs` (not plain `BaseModel`) when their fields need to be forwarded as `**kwargs` to a third-party constructor. `to_kw(exclude_none=True)` flattens a nested `kwargs` dict at the top level.

**`LaifeParams` singleton**
Access project-wide config and paths via `get_laife_params()` from `src/laife/params/laife_params.py`. Environment is controlled by `ENV_STAGE_TYPE` (`dev`/`prod`) and `ENV_LOCATION_TYPE` (`local`/`render`) env vars.
Credentials live at `~/cred/laife/.env`, loaded by `load_env()` in `src/laife/params/load_env.py`; `nokeys.env` lists the keys.

**`to_prompt()` convention**
Every entity and domain object that feeds into an LLM context exposes a `to_prompt() -> str` method. Build prompts by composing these, not by manually constructing strings.

## Code style

- Logging: `from loguru import logger as lg`; the structured game log is `slog` from `laife.meta.logger`.
- Docstrings: Google style, section labels with a trailing colon, never NumPy or RST underlines.
- Ruff runs with `select = ["ALL"]` (`ruff.toml`). Fix findings rather than adding `noqa`.

## Layout

- `tests/` mirrors `src/laife/`.
- `scripts/` holds scripts run directly, never imported or collected by pytest.
- `plans/` holds the plan folders, `plan.md` the backlog.
- `scratch_space/` holds throwaway notebooks and scripts; ruff is lenient there.
- `docs/` is the MkDocs site: `guides/` for concepts and tooling, `library/` for module notes.

## Spellcheck

When the spellchecker flags a technical term or a British/American spelling, add it to
`.vscode/settings.json` under `cSpell.words` rather than rewording around it.
