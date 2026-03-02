# Terrain entity

Create a `Terrain` class (forest, lake, fertile land) with position, size, and
terrain type. Implement `Vectorable`, `to_prompt(pov_pos)`, and
`to_document()`/`from_document()`. Add terrain instances to `WorldRunner` and
include them in `WorldMapObservation` so the player can perceive terrain when
observing. This unlocks dynamic map composition, prompt richness, and terrain
rendering.

---

## Plan

### New files

| File                                  | Purpose                                                                                              |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `src/laife/entities/terrain.py`       | `TerrainType` enum + `Terrain` pydantic model implementing `Vectorable`                              |
| `src/laife/entities/terrain_types.py` | Starter `TerrainType` instances (forest, lake, fertile_land, plain) analogous to `building_types.py` |
| `tests/entities/test_terrain.py`      | Unit tests for `Terrain` serialization and `to_prompt`                                               |

### Modified files

#### `src/laife/entities/terrain.py`

- `TerrainType` enum with values: `FOREST`, `LAKE`, `FERTILE_LAND`, `PLAIN`.
- `Terrain(BaseModel)`:
  - Fields: `name: str`, `terrain_type: TerrainType`, `position: Position`,
    `size: Size`, `description: str | None = None`.
  - `to_prompt(pov_pos: Position | None = None) -> str`: describes the terrain
    type, optional description, and direction/distance relative to `pov_pos`
    (mirrors `Building.to_prompt`).
  - `to_document() -> Document`: writes `entity_type = "terrain"` into metadata
    alongside all scalar fields.
  - `from_document(doc) -> Self`: reconstructs from `doc.metadata`.

#### `src/laife/entities/terrain_types.py`

- Module-level `TERRAIN_TYPES: list[Terrain]` with at least four starter
  instances covering the four `TerrainType` variants, each with a name, a fixed
  position and size, and a short description.

#### `src/laife/entities/world_runner.py`

- Add `self.terrains: list[Terrain] = []` alongside `self.buildings`.
- Add `add_terrain(terrain: Terrain) -> None` (mirrors `add_building`).
- In `_observe_nearby(position, radius)`: include nearby `Terrain` instances in
  the result using the same `euclidean` distance guard, with
  `entity_type = "terrain"`.
- Seed starter terrains from `terrain_types.py` inside `__init__` (or expose it
  as a separate `seed_world()` helper so tests can skip seeding).

#### `src/laife/entities/world_map_observation.py`

- `NearbyEntity.entity_type` already accepts any string - no model change needed.
- `to_prompt()`: no structural change; terrain entities appear automatically
  because they flow through `NearbyEntity`. Optionally special-case the
  description line for `entity_type == "terrain"` to be more natural ("A forest
  lies to the north").

#### `src/laife/rendering/world_renderer.py`

- Add a `_draw_terrains()` method called before buildings/players are rendered.
- Map each `TerrainType` to a fill color:
  - `FOREST` - dark green `(34, 85, 34)`
  - `LAKE` - steel blue `(70, 130, 180)`
  - `FERTILE_LAND` - olive `(107, 142, 35)`
  - `PLAIN` - tan `(210, 180, 140)`
- Draw each terrain as a filled `pygame.Rect` from `position` and `size` (in
  tile units, scaled by the same factor used for buildings). Replace the flat
  black `screen.fill((0, 0, 0))` call with a neutral background only for areas
  not covered by a terrain region.

#### `tests/entities/test_terrain.py`

- `test_terrain_to_document_round_trip`: `from_document(terrain.to_document())`
  reconstructs an equal object.
- `test_terrain_to_prompt_no_pov`: returns a non-empty string containing the
  terrain type name.
- `test_terrain_to_prompt_with_pov`: return value contains a cardinal direction.
- `test_terrain_implements_vectorable`: `isinstance(Terrain(...), Vectorable)`
  passes (structural check).

### Sequence of changes

1. Create `terrain.py` with `TerrainType` and `Terrain`; run tests to confirm
   the model serializes cleanly.
2. Create `terrain_types.py` with starter instances.
3. Extend `WorldRunner` with `terrains` list, `add_terrain`, and terrain seeding.
4. Update `_observe_nearby` to include terrain `NearbyEntity` entries.
5. Update `WorldMapObservation.to_prompt()` with a natural-language terrain line
   (optional but recommended).
6. Update `WorldRenderer._draw_terrains()`.
7. Write `tests/entities/test_terrain.py`.
8. Verify: `uv run pytest && uv run ruff check . && uv run pyright`.
