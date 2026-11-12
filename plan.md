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

### Renderer checks without a screen

The headless run skips `WorldRenderer`, so nothing an agent runs exercises the drawing code.
Checks specific to the renderer: SDL's dummy video driver, or frames saved to images and compared.
They depend on which renderer stays (item above).

### Runtime warnings

Folder `34_runtime_warnings` holds three drafted fixes: `SystemExit` on quit, the pydantic V1 warning on 3.14, pygame's AVX2 notice.

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

### Players that can die

An alive state on the player, and what ends it.

### Dynamic map

Load the map from data instead of the hardcoded setup in `game/main.py`.

## Code health

From folder 33 unless noted; each is checked against the code there.

### Judge after the collision check

`WorldRunner.judge_and_build()` pays for the LLM judge before the free collision check. Swap the order.

### One base for the LLM chain wrappers

Six classes build a `StructuredLLMChain` the same way. One generic base, config plus chain construction plus `invoke`/`ainvoke`, possibly in llm-core.

### World request boilerplate

Every `WRec*` forwards `*args, **kwargs` to `WReq.__init__` by hand; `@dataclass(kw_only=True)` would remove it.

### One logging call per event

`Player` and `WorldRunner` call `alg.log` and `slog` for the same event. One call that feeds both channels.

### Provider layering

Every chain takes the default OpenAI config; the Azure, HuggingFace and Ollama configs are built and never selected. Either use the choice or cut it.

### Singleton reset

The `Singleton` metaclass has no reset hook. Low priority: no test needs one yet.

### Duplicated `BaseModelKwargs`

Found 2026-11-12: `src/laife/data_models/basemodel_kwargs.py` and llm-core both define it.

### Install weight

Found 2026-11-12: `make sync` installs torch with the full CUDA 12 stack, through `transformers` and `llm-core[all]`, for a game that calls hosted models. Check what needs torch, and whether the CPU build or a narrower llm-core extra would do.
