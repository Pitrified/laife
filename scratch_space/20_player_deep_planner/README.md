# Player Deep Planner

## Goal

When the brain picks `ActionPlan`, the player is signalling it is stuck or the mission is too
broad to act on directly. The **planner** takes over: it reads the current mission, history, and
world observation, then uses an LLM to decompose the mission into an ordered list of concrete
sub-missions. The result is written back into `Mission.steps` so the next `think()` call has a
tighter, actionable target.

---

## Patterns followed

| Reference                           | What to borrow                                                                                    |
| ----------------------------------- | ------------------------------------------------------------------------------------------------- |
| `src/laife/llm/structured_chain.py` | `StructuredLLMChain[InputT, OutputT]` as the backbone                                             |
| `src/laife/entities/world_judge.py` | `@dataclass` component with `XInput(BaseModelKwargs)` + `XResult(BaseModel)` + `X.invoke/ainvoke` |
| `src/laife/entities/action.py`      | `ActionPlan` is the trigger; the planner runs inside `Player.plan()`                              |
| `src/laife/llm/mission.py`          | `Mission.add_sub_mission()` mutates the tree; planner writes into it                              |
| `src/laife/llm/player_brain.py`     | `PlayerBrainConfig(BaseModel)` + `PlayerBrain` as the config/class split                          |
| `src/laife/llm/prompt_loader.py`    | `PromptLoaderConfig` + versioned Jinja prompt in `prompts/player_planner/v1.jinja`                |

---

## New files

```
src/laife/llm/player_planner.py         # PlayerPlannerConfig + PlayerPlanner
src/laife/prompts/player_planner/v1.jinja
tests/llm/test_player_planner.py
```

---

## Data models

### `PlayerPlannerInput(BaseModelKwargs)` - in `player_planner.py`

Fields drive required Jinja template variables (same guard as `StructuredLLMChain`):

| Field          | Type  | Description               |
| -------------- | ----- | ------------------------- |
| `mission`      | `str` | `mission.to_prompt()`     |
| `history`      | `str` | `history.to_prompt()`     |
| `observation`  | `str` | `observation.to_prompt()` |
| `player_state` | `str` | `player.render_state()`   |

### `PlayerPlannerResult(BaseModel)` - in `player_planner.py`

What the LLM returns structured:

| Field          | Type        | Description                                           |
| -------------- | ----------- | ----------------------------------------------------- |
| `sub_missions` | `list[str]` | Ordered sub-mission objectives; at least one required |
| `reason`       | `str`       | Why these sub-missions make sense                     |

---

## Classes

### `PlayerPlannerConfig(BaseModel)` - in `player_planner.py`

```python
class PlayerPlannerConfig(BaseModel):
    chat_config: ChatConfig
    prompt_loader_config: PromptLoaderConfig
```

### `PlayerPlanner` - `@dataclass` in `player_planner.py`

```python
@dataclass
class PlayerPlanner:
    config: PlayerPlannerConfig

    def __post_init__(self) -> None:
        prompt_str = PromptLoader(self.config.prompt_loader_config).load_prompt()
        self._chain: StructuredLLMChain[PlayerPlannerInput, PlayerPlannerResult] = (
            StructuredLLMChain(
                chat_config=self.config.chat_config,
                prompt_str=prompt_str,
                input_model=PlayerPlannerInput,
                output_model=PlayerPlannerResult,
            )
        )

    async def ainvoke(self, planner_input: PlayerPlannerInput) -> PlayerPlannerResult: ...
    def invoke(self, planner_input: PlayerPlannerInput) -> PlayerPlannerResult: ...
```

---

## Prompt - `prompts/player_planner/v1.jinja`

Template variables must exactly match `PlayerPlannerInput` fields.
Responsibilities:

- Describe the role: you are a strategic planner for an autonomous agent in a survival sim.
- Provide context: mission, history, observation, player state.
- Request: return an ordered list of sub-missions that, when executed in sequence, will complete
  the top-level mission. Each sub-mission must be short, concrete, and achievable in a few actions.

---

## Integration into `Player`

### `Player.__init__` - add `self.planner`

```python
self.planner = PlayerPlanner(
    PlayerPlannerConfig(
        chat_config=laife_params.llm_services.chat.default,
        prompt_loader_config=PromptLoaderConfig(
            base_prompt_fol=laife_params.paths.prompts_fol,
            prompt_name="player_planner",
        ),
    )
)
```

### `Player.plan()` - replace the sleep stub

Current body sleeps 1 second and returns a dummy `WRes`. Replace with:

1. Build `PlayerPlannerInput` from current state.
2. Call `await self.planner.ainvoke(planner_input)`.
3. For each `sub_mission` in `result.sub_missions`, call `self.mission.add_sub_mission(sub_mission)`.
4. Reset `self.history` to a fresh `MissionHistory()` so the next `think()` starts clean.
5. Log the new sub-missions.
6. Return `WRes(WResStatus.SUCCESS, {"sub_missions": result.sub_missions, "reason": result.reason})`.

---

## Play loop interaction

```
play()
  observe()
  think() -> ActionPlan          # brain signals it needs to replan
  plan(ActionPlan)
    planner.ainvoke(...)         # LLM decomposes mission into sub_missions
    mission.add_sub_mission(...) # for each sub_mission
    history = MissionHistory()   # reset
  -> WRes(SUCCESS)
  history.add_history_entry(ActionPlan, wrsp)
  # next iteration: think() sees mission with steps, picks a concrete action
```

---

## Tests - `tests/llm/test_player_planner.py`

Mirror `tests/llm/test_player_brain.py` structure:

| Test                                  | What it checks                                                          |
| ------------------------------------- | ----------------------------------------------------------------------- |
| `test_config_is_valid`                | `PlayerPlannerConfig` instantiates with valid fields                    |
| `test_ainvoke_passes_correct_kwargs`  | `ainvoke` calls the chain with the right `PlayerPlannerInput`           |
| `test_ainvoke_returns_result`         | mocked chain returns a `PlayerPlannerResult`; planner passes it through |
| `test_plan_handler_adds_sub_missions` | `Player.plan()` calls `mission.add_sub_mission` once per sub-mission    |
| `test_plan_handler_resets_history`    | after `Player.plan()`, `player.history.history` is empty                |
| `test_plan_handler_returns_success`   | `Player.plan()` returns `WRes(WResStatus.SUCCESS, ...)`                 |

---

## Implementation order

1. `prompts/player_planner/v1.jinja` - prompt first, drives all variable names.
2. `src/laife/llm/player_planner.py` - `PlayerPlannerInput`, `PlayerPlannerResult`, `PlayerPlannerConfig`, `PlayerPlanner`.
3. `tests/llm/test_player_planner.py` - unit tests with mocked chain.
4. Wire into `src/laife/entities/player.py` - add `self.planner`, replace `plan()` body.
5. Verify: `uv run pytest && uv run ruff check . && uv run pyright`.
