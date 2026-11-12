# World Mission Controller

In `src/laife/entities/action.py` we have a sample pattern for how to interface with a LLM in a
structured way.

We now need to define a similar pattern for the world, so that it can decide if an action is valid
or not, and give feedback to the player about it, both in the case of success and failure.

Example: a player wants to craft a wooden pickaxe, using a piece of wood and a piece of stone. The
player sends a request to the world to craft the pickaxe. With these materials the pickaxe can be
crafted, BUT only if the player is near a crafting table. In the player observation we have the
description of the world around the player, so the world does know if the player is near a crafting
table or not. Given all these internal world rules, the world can decide if the crafting action is
successful or not, and send a response to the player with the result, and a feedback message that
can be used in the prompt to explain the result.

No need to check inventories - the player will pick the materials from its internal inventory, and
send those to the world, which will check if the crafting is possible with those materials.

---

## Action analysis

| Action        | World rules                                                                     | LLM judge needed?                            |
| ------------- | ------------------------------------------------------------------------------- | -------------------------------------------- |
| `ActionMove`  | AABB spatial collision only                                                     | No - fast rule-based geometry, already works |
| `ActionBuild` | Space available, player is at a valid build site, materials match               | Yes                                          |
| `ActionCraft` | Player is near the required station (e.g. crafting table), materials sufficient | Yes                                          |
| `ActionPlan`  | Player-internal reflection, no world interaction                                | No - always succeeds                         |

Move and Plan never need an LLM. Only **Build** and **Craft** require world judgement, and for both
the key context is identical: what the player wants, the observation of the world around them, and
the player state.

---

## Core pattern: `WorldActionJudge`

Mirror of `ActionPicker`:

```
ActionPicker:  prompt + chat model  ->  ActionEnvelope   (what to do)
WorldActionJudge:  prompt + chat model  ->  WorldJudgeResult  (was it valid?)
```

### Data structures

```python
class WorldJudgeInput(BaseModelKwargs):
    action_type: str      # "build" | "craft"
    action_details: str   # action fields serialised to prompt string
    observation: str      # player.last_observation
    player_state: str     # player.render_state()

class WorldJudgeResult(BaseModel):
    success: bool
    feedback: str         # natural-language outcome fed back into MissionHistory
```

### `WorldActionJudge` dataclass

Same `__post_init__` / `invoke` / `ainvoke` skeleton as `ActionPicker`. One class, two instances on
`WorldRunner` - one per prompt variant:

```python
world_runner.build_judge = WorldActionJudge(chat_config, build_prompt)
world_runner.craft_judge = WorldActionJudge(chat_config, craft_prompt)
```

Per-action prompt tuning without any code duplication. `WorldJudgeInput` uses the same
`_REQUIRED_PROMPT_VARS` guard to keep prompt templates and input fields in sync.

---

## Communication flow changes

### New request type `WRecCraft`

```python
class WRecCraft(WReq):
    utensil_name: str
    description: str
    observation: str      # player passes its own cached observation
    player_state: str
```

### Update `WRecBuild`

Add `observation: str` and `player_state: str` so the judge has world context.

### `WorldRunner.handle_player_input`

```
WRecBuild  ->  await build_judge.ainvoke(...)  ->  WRes with feedback
WRecCraft  ->  await craft_judge.ainvoke(...)  ->  WRes with feedback
```

`WRes.response_data` gets a `"feedback"` key so `MissionHistoryEntry` records a natural-language
outcome.

### `Player.build()` and `Player.craft()`

Pass `observation=self.last_observation` and `player_state=self.render_state()` when constructing
the request.

---

## Files to create / modify

| File                                           | Change                                                          |
| ---------------------------------------------- | --------------------------------------------------------------- |
| `src/laife/entities/world_judge.py`            | New - `WorldJudgeInput`, `WorldJudgeResult`, `WorldActionJudge` |
| `src/laife/prompts/world_judge_build/v1.jinja` | New - build validation prompt                                   |
| `src/laife/prompts/world_judge_craft/v1.jinja` | New - craft validation prompt                                   |
| `src/laife/entities/world_channel.py`          | Add `WRecCraft`; extend `WRecBuild` with observation fields     |
| `src/laife/entities/world_runner.py`           | Wire up judges for build and craft; remove stubs                |
| `src/laife/entities/player.py`                 | Pass `observation` and `player_state` in `build()` / `craft()`  |
| `tests/entities/test_world_judge.py`           | New unit tests                                                  |
