# Building split in general and instance

## Context

The current `Building` dataclass in `src/laife/entities/building.py` conflates
two kinds of data: master data that belongs to a building _type_, and instance
data that belongs to a specific building placed in the world.

Separating them prepares the ground for feature 16, where `BuildingType` will
be stored in the vector DB so the world can do semantic look-ups (e.g. "shelter"
→ "house").

---

## Data model split

### `BuildingType` (new, general / master data)

Fields that describe a category of building and never change per instance:

| field           | type   | notes                             |
| --------------- | ------ | --------------------------------- |
| `building_type` | `str`  | primary key, e.g. `"house"`       |
| `description`   | `str`  | human-readable purpose            |
| `size`          | `Size` | canonical footprint for this type |

Currently lives as the module-level `BUILDING_TYPES` list and `BUILDING_DESCRIPTIONS`
dict on `Building`. Move everything into a Pydantic `BaseModel`; the description
field on `BuildingType` replaces `BUILDING_DESCRIPTIONS` entirely.

### `Building` (updated, instance data)

`Building` is already a Pydantic `BaseModel`. Fields that vary per placed building:

| field           | type           | notes                           |
| --------------- | -------------- | ------------------------------- |
| `name`          | `str`          | player-visible label            |
| `position`      | `Position`     | world coordinates               |
| `building_type` | `BuildingType` | reference to the type           |
| `description`   | `str \| None`  | optional instance-specific note |

Replace the bare `building_type: str` field with `building_type: BuildingType`.
`size` moves off `Building` onto `BuildingType`.

---

## Steps

1. **Add `BuildingType` BaseModel** in `building.py`
   - fields: `building_type`, `description`, `size`
   - remove `BUILDING_TYPES` list and `BUILDING_DESCRIPTIONS` dict; description
     is now carried by each `BuildingType` instance

2. **Create `building_types.py`** in `src/laife/entities/`
   - contains a pre-built set of `BuildingType` instances (`HOUSE`, `FARM`, `FACTORY`)
   - add a module docstring explaining these are a *starting set*, used to
     create the initial world state and pre-populate the vector DB in a later feature

3. **Update `Building` BaseModel**
   - change `building_type: str` → `building_type: BuildingType`
   - remove `size` field (now on the type)
   - keep `description` for instance-level overrides
   - update `to_prompt` to read `self.building_type.description` and
     `self.building_type.size`

4. **Update `__str__`** to remain human-readable

5. **Update call-sites**
   - `src/laife/entities/world_runner.py` (or wherever buildings are
     constructed) - pass a `BuildingType` object instead of a bare string
   - rendering code that reads `size` - now reads `building.building_type.size`

6. **Update tests**
   - any test that builds a `Building(...)` directly needs to supply a
     `BuildingType` instead of a string

---

## Out of scope for this feature

- Making `BuildingType` vectorable (feature 16)
- Dynamic player-created building types
- Persistence / serialization of `BuildingType`
