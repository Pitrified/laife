# World map observation

Convert some area of the world around a player into a structured description that can be used in the prompt,
and also as a way for the player to build an internal representation of the world.

Define a `WorldMapObservation` class that includes the player's position and a list of nearby entities with their relative positions.

The `WorldMapObservation` will have a `to_prompt()` method that converts it into a text description for the LLM.

## Problem

`WorldRunner.describe_world()` currently returns a hardcoded placeholder string (see `world_runner.py`).
`Player.last_observation` is a plain `str`, which is sufficient for passing the text to the LLM but loses
all structure. The LLM prompt therefore contains no real spatial information about the world: player position,
nearby buildings, other players, or distances.

## Goal

Replace the placeholder with a rich, structured `WorldMapObservation` object that:

1. Is produced by `WorldRunner` from its authoritative entity state.
2. Travels back to the player via the existing `WRes` / `WRecObserve` channel.
3. Deserialises cleanly on the player side so `last_observation` can carry real data.
4. Exposes `to_prompt() -> str` for LLM consumption, following the project-wide convention.

## Design

### `WorldMapObservation` data class

Location: `src/laife/entities/world_map_observation.py`

```
WorldMapObservation
  player_position: Position          # absolute (left, top)
  nearby_entities: list[NearbyEntity]
```

```
NearbyEntity
  entity_type: str          # "building" | "player"
  name: str
  relative_position: Position   # (dx, dy) from observing player
  distance: float               # Chebyshev or Euclidean - pick one consistently
```

The observation radius (how far away entities are included) is a parameter with a sensible default (e.g. 20 tiles).

### `to_prompt()` output

Human-readable text intended for the LLM context, for example:

```
You are at position (10, 5).
Nearby entities (within 20 tiles):
- Building "Woodcutter Hut" is 3 tiles east and 2 tiles north (distance 3.6).
- Player "Yuki" is 1 tile west (distance 1.0).
Nothing else is nearby.
```

Use cardinal direction words (`north`, `south`, `east`, `west`, or combinations) derived from the relative
position vector, consistent with `src/laife/entities/utils/directions.py` conventions.

### Changes to `WorldRunner`

- `WRecObserve` gains a `position: Position` field. The runner only needs the observing position to
  compute relative offsets - it does not need to know which player is asking.
- `WorldRunner.describe_world()` is replaced by `WorldRunner.observe_at(position)` which builds and
  returns a `WorldMapObservation`.
- `WRes.response_data["observation"]` holds the `WorldMapObservation` object directly (not a string).

### Changes to `Player`

- `last_observation: WorldMapObservation` replaces `last_observation: str`. Initialised in `__init__`
  with an empty `WorldMapObservation` for `self.position` so there is no `None` to guard against.
  It may be stale for a single tick but is refreshed on the first `observe()` call.
- `observe()` stores the rich object directly; `to_prompt()` is called only at the point the
  observation is injected into the LLM prompt (e.g. inside `PlayerBrain.think()`).
- `WRecObserve` is constructed with `position=self.position`.

## Migration notes

- No other callers of `describe_world()` exist; it is safe to rename/replace.
- Existing tests that mock `WRes` with `{"description": "..."}` must be updated to use
  `{"observation": <WorldMapObservation instance>}`. There is no fallback - the old key is removed.

## File plan

| File                                           | Action                                                                                                     |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `src/laife/entities/world_map_observation.py`  | Create - `NearbyEntity`, `WorldMapObservation`                                                             |
| `src/laife/entities/world_channel.py`          | Edit - add `position: Position` field to `WRecObserve`                                                     |
| `src/laife/entities/world_runner.py`           | Edit - replace `describe_world()` with `observe_at(position)`                                              |
| `src/laife/entities/player.py`                 | Edit - `last_observation` type; pass `position=self.position` in `WRecObserve`; unpack `"observation"` key |
| `src/laife/llm/player_brain.py`                | Edit - call `observation.to_prompt()` when building the LLM prompt                                         |
| `tests/entities/test_world_map_observation.py` | Create - unit tests for `WorldMapObservation.to_prompt()`                                                  |

## Out of scope

- Terrain / `Utensil` entities in the observation (can be added in a later scratch space).
- Caching or incremental updates to the observation.
