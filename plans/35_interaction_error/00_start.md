# interaction weirdness - bootstrap

Spun out of the observability effort:
[`32_observability/05.1_random_decisions.md`](../32_observability/05.1_random_decisions.md)
captured a live run where an interaction killed the whole game.
This folder investigates and fixes that failure mode.

## The captured incident

From the log (full trace in the 05.1 file):

```log
PLAYER.play p0: picked reason='To gather crops from the Big ol Farm, ...'
  target_name='Big ol Farm' message='I would like to gather crops.'
PLAYER.interact p0: messaging 'Big ol Farm'
W: Got player input: WRecInteract(... target='Big ol Farm' ...)
...
TypeError: Expected WResInteract, got WResError
make: *** [Makefile:25: run] Error 1
```

Plus a pydantic serializer UserWarning in the same run:
`Expected 'none' - serialized value may not be as expected [field_name='parsed',
input_value=ActionEnvelope(...)]`.

## Analysis (from reading the code, not the log alone)

The crash is three layered issues:

1. **The LLM targeted a building.**
   `ActionInteract.target_name` is documented as "Name of the player to address"
   (`src/laife/entities/action.py`), but the model picked `'Big ol Farm'` - a building.
   The observation prompt presumably lists buildings by name next to players,
   and nothing constrains or validates the target.
   Arguably the model's intent (gather crops from a farm) is reasonable;
   the action vocabulary just has no way to express it.
2. **The world answers with an error, correctly.**
   `WorldRunner.route_interaction` (`world_runner.py:148`) looks the target up
   among `self.players`, finds nothing, and returns
   `WResError("No player named 'Big ol Farm' exists ...")`. This part is fine.
3. **The player treats the error as a channel bug and dies.**
   `Player._world_request` (`player.py:317`) asserts the response type and raises
   `TypeError` on mismatch. Its docstring says a mismatch "signals a world
   implementation bug and should fail loudly" - but `WResError` is a documented,
   legitimate response (`route_interaction` is typed `WResInteract | WResError`).
   The contract and the channel typing disagree; one wrong LLM pick ends the process.

The pydantic warning is separate: the structured-output path serializes an object
whose `parsed` field is typed as expected-`none` but holds an `ActionEnvelope`
(langchain structured output / include_raw serialization). Harmless so far,
but worth pinning down before it hides a real schema drift.

## Decisions

- Fix resilience first (phase 1): the game must survive a `WResError` regardless
  of why the bad target was picked. An error response becomes a turn outcome the
  player can observe (and feed back to the brain as history), not a crash.
- Then investigate targeting (phase 2): what the observation offers as names,
  whether `ActionInteract` should validate targets, and whether "interact with a
  building" deserves its own action instead of being an error.
  This is the investigation part; it may end in a design change, not a patch.
- The serializer warning is phase 3, independent of the other two.

## Open questions

- Should `_world_request` return `T | WResError` (every caller handles errors),
  or should error handling live once in `Player.play()` around the action dispatch?
  ANS: widen `_world_request` to `T | WResError` - the `play()` dispatch already
  funnels every response into a history entry, and the helpers' post-request
  code must short-circuit on error anyway, which the widened type forces
  explicitly. Reasoning in [`01_survive_wres_error.md`](01_survive_wres_error.md#decisions).
- Is building interaction a missing feature (gathering crops is a sensible goal)
  or should the prompt steer the model away from non-player targets?
- Does the `parsed`-field warning come from our `StructuredLLMChain` usage or
  from inside langchain, and does it indicate a schema we should tighten?
