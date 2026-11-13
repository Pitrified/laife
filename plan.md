# Backlog

Future work, unnumbered and in no particular order.
An item becomes a numbered folder under `plans/` when it is picked for implementation, in the `tracked-development` layout; the item is then removed from here and the folder's `00_start.md` starts from its text.
What is already built is in the `done` folders under `plans/`; `python3 scripts/plans.py list --status done` lists them.

## Engine

### Renderer: pygame or a web app

Whether pygame stays as the renderer.
Options: pygame as now; a text-only runner beside a renderer (`scratch_space/rebirth_/` had it); a web page reading the world state, served from g7 over the tailnet and opened from g4 or the phone, as the sibling repo abyss does.
Also decides the Python pin: pygame 2.6 has no 3.14 wheel, and the `==3.14.*` pin uses nothing newer than 3.12 (folder 33).
The visual wishes wait on this choice: tiled terrain and grass instead of flat colours, buildings with a garden, utensils held by the player, a window that shows more state and answers the mouse.
The same pass trims the engine's terminal output and the logs.
The terminal is not the main interface: the window and `make tui` are.
Today a run prints every `alg.log` line, and the structured log has one line per move step; whether the structured log keeps its shape is reassessed with it.

### Renderer checks without a screen

The headless run skips `WorldRenderer`, so nothing an agent runs exercises the drawing code.
Checks specific to the renderer: SDL's dummy video driver, or frames saved to images and compared.
They depend on which renderer stays (item above).

### Runtime warnings

`SystemExit` on quit and pygame's AVX2 notice, drafted in folder `34_runtime_warnings` and parked there until the renderer is decided.

### Seed for the live game

`setup_world()` takes a `random.Random`; the headless run seeds it, `game/main.py` passes an unseeded one.
A `--seed` argument or an env var would make a live run start from a known world (folder 38).

### Recorded replay for the headless run

The headless run answers from a fixed script.
Replaying a live run's recorded answers would use the same seam, `ScriptedChatConfig` per player; it diverges as soon as the world differs from the recording, so it waits for a case that needs it (folder 38).

### A failed reply stops the world

An exception in the target's `receive_message()` escapes `WorldRunner.route_interaction` and ends `WorldRunner.simulate()`: the live game stops with a traceback, the headless run re-raises it.
The other choice is a `WResError` to the sender, as other world errors are handled since folder 35. Whether a failed reply should end the game is a gameplay decision (folder 38).

## Gameplay

### Starting utensils and the vector store in play

Define the starter utensils (bucket, axe, hammer, hoe) and seed them into the Chroma store with the building and terrain types.
Give the brain a retrieval step, so it looks up relevant utensils and buildings before choosing an action.
`ChromaConfig` is built and nothing in play queries it (folder 33).
Folder `31_utensil_crafting` holds the analysis of crafting a utensil that does not exist yet, including generating an image of it.

### Interaction memory

When a player receives a message, keep the content and sender, so the brain recalls past interactions when it replies.
`Player.receive_message()` replies and keeps nothing (folder 33).
A longer-term memory beyond the mission history is the same item grown.

### Interaction v2

The async-inbox strategy proposed in `24_player_interaction/00.1_strategy2_upgrade.md`: interactions that scale past a few players and allow broadcast.

### Shared missions

A player shares its mission with the world and can ask others for help.

### The complete judge sees no history

A live run on gpt-6-luna (2026-11-13, folder 34): a player moved 10 steps east, claimed its mission "move 10 steps east" complete, and the complete judge rejected it.
Its feedback: the current position is known, but no starting position or other evidence confirms the move.
The player then moved east again to make the move "recorded".
`WorldRunner.judge_complete()` gets the objective, the player's own claimed outcome, the observation and `Player.render_state()` (name, position, state); not the mission history. So a mission about moving cannot be confirmed.

### Players that can die

An alive state on the player, and what ends it.

### Dynamic map

Load the map from data instead of the hardcoded setup in `game/main.py`.

## Code health

From folder 33 unless noted; each is checked against the code there.

### One base for the LLM chain wrappers

Six classes build a `StructuredLLMChain` the same way. One generic base, config plus chain construction plus `invoke`/`ainvoke`, possibly in llm-core.

### World request boilerplate

Every `WRec*` forwards `*args, **kwargs` to `WReq.__init__` by hand; `@dataclass(kw_only=True)` would remove it.

### One logging call per event

`Player` and `WorldRunner` call `alg.log` and `slog` for the same event. One call that feeds both channels.

### Provider layering

Every chain takes the default OpenAI config; the Azure, HuggingFace and Ollama configs are built and never selected. Either use the choice or cut it.
`Player` and `WorldRunner` each take a `chat_config` (folder 38), so the world and the players can run different models, such as a stronger judge; nothing in the live game selects one yet.

### Scripted chat model to llm-core

`laife.llm.scripted_chat` answers structured-output calls by schema.
The model and config are general and could sit beside llm-core's `FakeChatModel`, which cycles one list regardless of schema; the default script and the per-schema answers stay in laife.
Moving it means an llm-core release and a tag bump here (folder 38).

### Singleton reset

The `Singleton` metaclass has no reset hook. Low priority: no test needs one yet.

### Duplicated `BaseModelKwargs`

Found 2026-11-12: `src/laife/data_models/basemodel_kwargs.py` and llm-core both define it.

### Install weight

Found 2026-11-12: `make sync` installs torch with the full CUDA 12 stack, through `transformers` and `llm-core[all]`, for a game that calls hosted models. Check what needs torch, and whether the CPU build or a narrower llm-core extra would do.
