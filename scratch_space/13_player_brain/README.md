# Player brain

The player brain is responsible for in general interacting with the language model.

---

## Current state of the codebase

- `entities/action.py`: `BaseAction`, `ActionMove`, `ActionBuild`, `ActionCraft`, `ActionPlan`, `Actions` union, `ActionEnvelope`, `ActionPicker` (chain wrapping `ChatConfig`)
- `llm/player_brain.py`: `PlayerBrain` stub — hardcoded ollama, translation prompt, no config injection; `think(query: str) -> str` not yet returning `BaseAction`
- `llm/mission.py`: `Mission`, `MissionHistory`, `MissionHistoryEntry`, `MissionStatus` — `to_prompt()` on all of them
- `entities/player.py`: `Player` with `play()` loop; `think()` returns a hardcoded `ActionMove`; all action handlers are stubs
- `llm_services/chat/config/base.py`: `ChatConfig(BaseModelKwargs)` with `create_chat_model()`
- `params/laife_paths.py`: `LaifePaths` with `src_fol`, `root_fol`, etc. via `LaifeParams` singleton

---

## Implementation plan

### Phase 1 — PromptLoader infrastructure

**Files:** `src/laife/llm/prompt_loader.py`, `src/laife/prompts/player_brain/v1.jinja`

1. Create `src/laife/prompts/player_brain/v1.jinja` — system prompt template with placeholders for mission, history, observation, player_state, actions_schema; leave rendering for later phases
2. Add `prompts_fol` to `LaifePaths.load_common_config_pre()` pointing to `src/laife/prompts/`
3. Create `PromptLoaderConfig(BaseModel)` with fields: `base_prompt_fol: Path`, `prompt_name: str`, `version: str` (default `"auto"`)
   - expected file path: `base_prompt_fol / prompt_name / f"v{version}.jinja"`
4. Create `PromptLoader` dataclass accepting `PromptLoaderConfig`:
   - `_resolve_version() -> str`: if `version == "auto"`, scan `base_prompt_fol / prompt_name /` for `vN.jinja` files and return the highest N; else return config version as-is
   - `load_prompt() -> str`: read and return raw jinja string; cache result in `_prompt_cache: str | None`
   - `prompt_str = PromptLoader(config).load_prompt()`

---

### Phase 2 — PlayerBrainConfig + refactored PlayerBrain

**Files:** `src/laife/llm/player_brain.py`

1. Create `PlayerBrainConfig(BaseModel)` with:
   - `chat_config: ChatConfig`
   - `prompt_loader_config: PromptLoaderConfig`
2. Rewrite `PlayerBrain.__init__(config: PlayerBrainConfig)`:
   - drop hardcoded ollama
   - instantiate model via `config.chat_config.create_chat_model()`
   - load raw prompt string via `PromptLoader(config.prompt_loader_config).load_prompt()`
   - store config for use by `think()`; leave `ActionPicker` wiring for Phase 4
3. Remove obsolete `chat()`, `achat()`, `llm_think()`, `naive_think()` methods (or mark deprecated)

---

### Phase 3 — ActionObserve + player observation state

**Files:** `src/laife/entities/action.py`, `src/laife/entities/player.py`, `src/laife/entities/world_runner.py`

1. Add `ActionObserve(BaseAction)` to `action.py` — no extra fields beyond `reason`
2. Add `ActionObserve` to the `Actions` union
3. `Player.__init__`: add `self.last_observation: str = ""`
4. `Player.play()` match block: add `case ActionObserve() as act: wrsp = await self.observe(act)`
5. `Player.observe(action: ActionObserve) -> WRes`: stub — sends a `WReq` to world, sets `self.last_observation = wrsp.data["description"]`, returns `WRes`
6. `WorldRunner` (or world channel): add stub handler for observe requests that returns a placeholder description string; mark with `# TODO: implement real world description`

---

### Phase 4 — ActionPicker context enrichment

**Files:** `src/laife/entities/action.py`

1. Extend `action_template_str` (or replace with the loaded jinja string) to include all context variables:
   - `{mission}`, `{history}`, `{observation}`, `{player_state}`, `{actions_schema}`
2. Update `ActionPicker.__post_init__`: accept `prompt_str: str` parameter; build `ChatPromptTemplate` from it instead of the hardcoded string; keep `with_structured_output(ActionEnvelope)`
3. Update `ActionPicker.invoke` / `ainvoke` signatures to:
   ```python
   def invoke(self, mission: str, history: str, observation: str, player_state: str) -> BaseAction
   ```
4. Populate `actions_schema` by extracting the JSON schema from `ActionEnvelope.model_json_schema()` and injecting it as a static string in the prompt

---

### Phase 5 — Wire Player.think() through PlayerBrain

**Files:** `src/laife/entities/player.py`, `src/laife/llm/player_brain.py`

1. `PlayerBrain.__post_init__` (or `__init__`): instantiate `ActionPicker(chat_config=config.chat_config, prompt_str=loaded_prompt)`
2. `PlayerBrain.think(mission: Mission, history: MissionHistory, observation: str, position: Position) -> BaseAction`:
   - call `self.action_picker.ainvoke(mission=mission.to_prompt(), history=history.to_prompt(), observation=observation, player_state=str(position))`
   - return the resulting `BaseAction`
3. `Player.__init__`: construct `PlayerBrainConfig` using `LaifeParams()` paths and `ChatConfig` (read from env/config); pass to `PlayerBrain(config)`
4. `Player.think()`: replace hardcoded `ActionMove` stub with:
   ```python
   return await self.brain.think(self.mission, self.history, self.last_observation, self.position)
   ```
5. `Player.play()`: ensure `ActionObserve` is dispatched first each loop iteration before calling `think()`, so `last_observation` is always fresh

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

