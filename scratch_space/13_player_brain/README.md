# Player brain

The player brain is responsible for in general interacting with the language model.

---

## Current state of the codebase

- `entities/action.py`: `BaseAction`, `ActionMove`, `ActionBuild`, `ActionCraft`, `ActionPlan`, `ActionObserve`, `Actions` union, `ActionEnvelope`, `MissingPromptVariablesError`, `ActionPicker(chat_config, prompt_str)` ✅
- `entities/world_channel.py`: `WReq`, `WRes`, `WRecBuild`, `WRecObserve` ✅
- `entities/world_runner.py`: `WorldRunner` with `describe_world()` stub ✅
- `llm/player_brain.py`: `PlayerBrainConfig`, `PlayerBrain(config)` — owns `ActionPicker`; `think(mission, history, observation, player_state) -> BaseAction` fully wired ✅
- `llm/prompt_loader.py`: `PromptLoaderConfig`, `PromptLoader`, `NoPromptVersionFoundError` ✅
- `llm/mission.py`: `Mission`, `MissionHistory`, `MissionHistoryEntry`, `MissionStatus` — `to_prompt()` on all of them
- `entities/player.py`: `Player` with `play()` loop (observe-then-think); `think()` calls `brain.think()`; `observe()` refreshes `last_observation`; `PlayerBrainConfig` built from `LaifeParams` ✅
- `llm_services/chat/config/base.py`: `ChatConfig(BaseModelKwargs)` with `create_chat_model()`
- `params/laife_paths.py`: `LaifePaths` with `src_fol`, `root_fol`, `prompts_fol`, etc. via `LaifeParams` singleton ✅
- `prompts/player_brain/v1.jinja`: system prompt template ✅

---

## Implementation plan

### Phase 1 — PromptLoader infrastructure ✅

**Files:** `src/laife/llm/prompt_loader.py`, `src/laife/prompts/player_brain/v1.jinja`

1. ✅ Created `src/laife/prompts/player_brain/v1.jinja` — system prompt template with placeholders for mission, history, observation, player_state; leave rendering for later phases
2. ✅ Added `prompts_fol` to `LaifePaths.load_common_config_pre()` pointing to `src/laife/prompts/`; also updated `__str__`
3. ✅ Created `PromptLoaderConfig(BaseModel)` with fields: `base_prompt_fol: Path`, `prompt_name: str`, `version: str` (default `"auto"`)
   - expected file path: `base_prompt_fol / prompt_name / f"v{version}.jinja"`
4. ✅ Created `PromptLoader` dataclass accepting `PromptLoaderConfig`:
   - `_resolve_version() -> str`: if `version == "auto"`, scan `base_prompt_fol / prompt_name /` for `vN.jinja` files and return the highest N; else return config version as-is
   - `load_prompt() -> str`: read and return raw jinja string; cache result in `_prompt_cache: str | None`
   - `prompt_str = PromptLoader(config).load_prompt()`

---

### Phase 2 — PlayerBrainConfig + refactored PlayerBrain ✅

**Files:** `src/laife/llm/player_brain.py`

1. ✅ Created `PlayerBrainConfig(BaseModel)` with:
   - `chat_config: ChatConfig`
   - `prompt_loader_config: PromptLoaderConfig`
2. ✅ Rewrote `PlayerBrain.__init__(config: PlayerBrainConfig)`:
   - dropped hardcoded ollama
   - instantiates model via `config.chat_config.create_chat_model()`
   - loads raw prompt string via `PromptLoader(config.prompt_loader_config).load_prompt()`
   - `think()` stubbed with `NotImplementedError`; `ActionPicker` wiring deferred to Phase 4
3. ✅ Removed obsolete `chat()`, `achat()`, `llm_think()`, `naive_think()` methods

---

### Phase 3 — ActionObserve + player observation state ✅

**Files:** `src/laife/entities/action.py`, `src/laife/entities/player.py`, `src/laife/entities/world_runner.py`, `src/laife/entities/world_channel.py`

1. ✅ Added `ActionObserve(BaseAction)` to `action.py` — no extra fields beyond `reason`
2. ✅ Added `ActionObserve` to the `Actions` union
3. ✅ `Player.__init__`: added `self.last_observation: str = ""`
4. ✅ `Player.play()` match block: added `case ActionObserve() as act: wrsp = await self.observe(act)` (before other cases)
5. ✅ `Player.observe(action: ActionObserve) -> WRes`: sends a `WRecObserve` to world, sets `self.last_observation = wrsp.response_data["description"]`, returns `WRes`
6. ✅ `WorldRunner.describe_world()`: stub returning placeholder description; `WRecObserve` added to `world_channel.py` and routed in `handle_player_input()`

---

### Phase 4 — ActionPicker context enrichment ✅

**Files:** `src/laife/entities/action.py`

1. ✅ Removed `action_template_str` and `action_prompt_template` module-level variables
2. ✅ Updated `ActionPicker` dataclass: added `prompt_str: str` field; `__post_init__` builds `ChatPromptTemplate` from it using `template_format="jinja2"`, validates required variables (`mission`, `history`, `observation`, `player_state`) via `MissingPromptVariablesError`
3. ✅ Updated `invoke` / `ainvoke` signatures to accept `mission`, `history`, `observation`, `player_state` and pass all four into the chain
4. ✅ ~~Inject `actions_schema` into the prompt~~ — not needed. `with_structured_output(ActionEnvelope)` already delivers the full field definitions to the model via the API's tool/function-calling mechanism. A raw JSON schema string in the prompt would be redundant and noisy. Describe actions semantically in the Jinja template if clarity is needed.

---

### Phase 5 — Wire Player.think() through PlayerBrain ✅

**Files:** `src/laife/entities/player.py`, `src/laife/llm/player_brain.py`

1. ✅ `PlayerBrain.__init__`: instantiates `ActionPicker(chat_config=config.chat_config, prompt_str=loaded_prompt)`; removed stale `self.llm` (owned by `ActionPicker` now)
2. ✅ `PlayerBrain.think(mission, history, observation, player_state) -> BaseAction`: calls `self.action_picker.ainvoke(...)` and returns the action
3. ✅ `Player.__init__`: constructs `PlayerBrainConfig` from `LaifeParams()` — `ChatParams(env_type).default` for the chat config, `prompts_fol / "player_brain"` for the prompt loader
4. ✅ `Player.think()`: replaced hardcoded `ActionMove` stub with `await self.brain.think(mission, history, last_observation, position)`
5. ✅ `Player.play()`: dispatches `ActionObserve` at the top of every loop iteration before calling `think()`

---

### Phase 6 — Tests

**Files:** `tests/llm/test_prompt_loader.py`, `tests/llm/test_player_brain.py`

1. `test_prompt_loader.py`:
   - test `version="auto"` resolution with a temporary directory containing `v1.jinja`, `v2.jinja`
   - test caching (same string returned on second call without re-reading disk)
   - test explicit version loads exact file
2. `test_player_brain.py`:
   - test `PlayerBrainConfig` instantiation
   - test `PlayerBrain.think()` with a mocked `ActionPicker` returning a known action

