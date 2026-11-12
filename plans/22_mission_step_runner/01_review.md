# small tweaks in mission step runner

we implemented
scratch_space/22_mission_step_runner/README.md
which is a good starting point but missing something

in particular, the world is the one that has to decide if a mission is completed

```python
async def complete(self, action: ActionComplete) -> WRes:
    """Mark the active focus mission done and advance to the next step."""
```

this function cannot be player only.

so either

- in ActionComplete we sent a message to the world to have a feedback on the mission completion.
- we do this every Player.play loop. which is probably too often but simpler to implement

## Decision: world round-trip on `ActionComplete`

Use option 1. Mirror the existing `WRecBuild` / `WRecCraft` pattern: the player sends a
`WRecComplete` request and only advances the mission tree if the world returns `SUCCESS`.
If the world returns `ERROR` the focus mission stays `ACTIVE` and the brain retries.

---

## Changes on top of README.md

### `src/laife/entities/world_channel.py` - new `WRecComplete`

```python
class WRecComplete(WReq):
    """Request the world to verify that a focus mission is done."""

    def __init__(
        self,
        objective: str,
        outcome: str,
        observation: str,
        player_state: str,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.objective = objective    # mission objective being closed
        self.outcome = outcome        # player-reported one-sentence outcome
        self.observation = observation
        self.player_state = player_state
```

### `src/laife/entities/world_runner.py` - new judge and handler

Initialise `complete_judge` alongside `build_judge` and `craft_judge` in `__init__`:

```python
complete_prompt = PromptLoader(
    PromptLoaderConfig(
        base_prompt_fol=laife_params.paths.prompts_fol,
        prompt_name="world_judge_complete",
    )
).load_prompt()
self.complete_judge = WorldActionJudge(
    chat_config=laife_params.llm_services.chat.default,
    prompt_str=complete_prompt,
)
```

Add `WRecComplete` to the import list and wire it in `handle_player_input`:

```python
case WRecComplete():
    wrsp = await self.judge_complete(player_input)
```

Implement `judge_complete` - reuses `WorldJudgeInput` / `WorldJudgeResult` unchanged:

```python
async def judge_complete(self, req: WRecComplete) -> WRes:
    """Ask the LLM judge whether the reported outcome satisfies the objective."""
    result = await self.complete_judge.ainvoke(
        WorldJudgeInput(
            action_type=f"complete: {req.objective}",
            action_details=req.outcome,
            observation=req.observation,
            player_state=req.player_state,
        )
    )
    alg.log(f"WR.judge_complete: {result.success} - {result.feedback}")
    return WRes(
        WResStatus.from_bool(success=result.success),
        {"feedback": result.feedback},
    )
```

### `src/laife/entities/player.py` - `Player.complete()` round-trips to the world

```python
async def complete(self, action: ActionComplete) -> WRes:
    """Ask the world to verify completion; advance only on SUCCESS."""
    focus = self.mission.active_focus()
    alg.log(f"PLAYER.complete {self.name}: requesting world verdict for '{focus.objective}'")
    wreq = WRecComplete(
        objective=focus.objective,
        outcome=action.outcome,
        observation=self.last_observation.to_prompt(),
        player_state=self.render_state(),
        response_queue=self.input_queue,
    )
    await self.world_input_queue.put(wreq)
    wrsp = await self.input_queue.get()
    self.input_queue.task_done()

    if wrsp.status == WResStatus.ERROR:
        # World rejected the claim - mission stays ACTIVE, brain will retry
        alg.log(f"PLAYER.complete {self.name}: world rejected - {wrsp.response_data}")
        return wrsp

    focus.status = MissionStatus.COMPLETED
    advanced = self.mission.advance()
    self.history = MissionHistory()
    next_label = self.mission.active_focus().objective if advanced else "all steps done"
    msg = f"Completed '{focus.objective}'. Next: '{next_label}'."
    alg.log(f"PLAYER.complete {self.name}: {msg}")
    return WRes(WResStatus.SUCCESS, {"message": msg, "outcome": action.outcome})
```

WRecComplete must also be added to the import block in `player.py`.

### `src/laife/prompts/world_judge_complete/v1.jinja` - new prompt

Reuses the same `WorldJudgeInput` fields (`action_type`, `action_details`, `observation`,
`player_state`) so no new model is needed. The prompt instructs the LLM to verify that
the stated outcome plausibly satisfies the mission objective given the current observation,
returning `{"success": true/false, "feedback": "..."}`.

---

## Updated data models summary (delta on README.md)

| Class / method                    | File                 | Change                                       |
| --------------------------------- | -------------------- | -------------------------------------------- |
| `WRecComplete`                    | `world_channel.py`   | new                                          |
| `WorldRunner.complete_judge`      | `world_runner.py`    | new judge, initialised in `__init__`         |
| `WorldRunner.judge_complete`      | `world_runner.py`    | new handler method                           |
| `WorldRunner.handle_player_input` | `world_runner.py`    | wire `WRecComplete` case                     |
| `Player.complete`                 | `entities/player.py` | send `WRecComplete`; advance only on SUCCESS |
| `world_judge_complete/v1.jinja`   | `prompts/`           | new prompt                                   |

The `WorldRunner` "no changes needed" note in README.md no longer applies.

---

## Test additions to `tests/entities/test_mission_step_runner.py`

| Test                                | What it checks                                                    |
| ----------------------------------- | ----------------------------------------------------------------- |
| `test_complete_world_rejected`      | when world returns ERROR, focus mission stays ACTIVE              |
| `test_complete_world_approved`      | when world returns SUCCESS, focus is COMPLETED and next activated |
| `test_complete_sends_wrec_complete` | `WRecComplete` lands on the world queue with correct fields       |
