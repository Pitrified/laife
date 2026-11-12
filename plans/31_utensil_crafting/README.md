---
status: draft - analyzed - unplanned
---

# Craft utensils

## draft

one of the possible missions is to craft a utensil

known utensils live in the vector db

for now we assume no inventory concepts, so all utensils are available to the player

the player can craft any utensil at any time, no crafting table required

but the player must have the materials, which are not really utensils, but still in the vector db
and materials do not exist

and the current inventory is a list of utensils

so

we need to analyze how entities are related to utensils and materials,
which superclasses they share, which shape could the inventory have

and in relation to the rest of the buildings/types/terrain, where do they live?
how do they relate?

## analysis

### what exists in code today

- `Utensil` (`src/laife/entities/utensil.py`): a plain Python class, just `name` + `description`.
  no position, no size, no type/instance split. implements `to_document` / `from_document`
  with `entity_type="utensil"`.
- `Building` + `BuildingType` (`src/laife/entities/building.py`): both pydantic `BaseModel`.
  `BuildingType` is master/catalogue data (type, description, size), `Building` is a placed
  instance with a `position`. both serialize to documents (`entity_type` "building" / "building_type").
- `Terrain` + `TerrainType` (`src/laife/entities/terrain.py`): `TerrainType` is a closed
  `StrEnum`, `Terrain` is a pydantic instance with position + size. serializes with `entity_type="terrain"`.
- `Player.inventory: list[Utensil]` (`player.py:146`). `craft()` (`player.py:432`) builds a
  `Utensil(name, description)` from the action and appends it on world SUCCESS.
- materials: **not modeled at all**. they appear only as free text in the craft judge prompt
  (`prompts/world_judge_craft/v1.jinja`: "are the described materials sufficient") and in the
  `ActionCraft` docstring. nothing in code supplies, stores, or consumes them.

### q1: shared superclass / how they relate

the common contract is **`Vectorable`** (`llm_core.vectorstores.vectorable`), a `@runtime_checkable`
*Protocol*, not a base class. anything with `to_document` + `from_document` (writing `entity_type`
into metadata) satisfies it. so utensils, buildings, building-types and terrain are siblings by
structure, not by inheritance.

two things break the symmetry:

1. **utensil is the odd one out.** `Building` and `Terrain` are pydantic `BaseModel`s; `Utensil`
   is a bare class. aligning it (make it a `BaseModel`) would make the whole entity family uniform.
2. **utensil has no type/instance split.** building has `BuildingType` (catalogue) vs `Building`
   (placed). terrain has `TerrainType` (enum) vs `Terrain` (placed). utensil has neither layer:
   one flat class doubles as both "known utensil in the catalogue" and "utensil in the inventory".

there is also a **semantic conflation**: `ActionCraft` deliberately separates *item* ("physical
object that can be used to solve a mission") from *utensil* ("device used to craft other items"),
but the code stores both as `Utensil` under the field `utensil_name`. materials would be a third
kind. so the design wants 3 concepts (item / utensil / material) and the code currently has 1.

### q2: where they live, relative to buildings / terrain

- **placed instances** (`Building`, `Terrain`) carry a `position` and live in the world map /
  `WorldRunner`. utensils and materials have no position - they are *not* on the map.
- **catalogue ("known" entities)** live in the vector db. note an unresolved inconsistency:
  `search.py` configures a single Chroma collection `collection_name="laife"`, while
  `config/constants.py` separately declares `UTENSILS_COLLECTION = "utensils"`. one of these
  patterns has to win (see options below).
- **inventory** is the only other home: `list[Utensil]` on the player. crucially, `craft()` does
  **not** look the utensil up in the vector db catalogue - it fabricates a new `Utensil` from the
  LLM action's name+description. so today the vector db and the inventory are disconnected.
- buildings have a seed catalogue (`BUILDING_TYPES`) and terrain has one (`TERRAINS`); there is
  **no** equivalent `utensil_types` / `UTENSILS` seed constant. the "known utensils live in the
  vector db" premise has no seeding code yet.

### open decisions this raises

1. **collection layout**: single `laife` collection filtered by `entity_type`, or one collection
   per kind (`utensils`, `materials`, ...)? the codebase currently contradicts itself.
2. **model material as an entity** (`Material`, `Vectorable`, no position, lives in catalogue +
   maybe inventory) vs keep it purely narrative and LLM-judged. the draft says "materials do not
   exist" - the question is whether to make them exist or formalize that they never will.
3. **inventory shape**: today it is a flat `list[Utensil]` with no quantity and no kind. if
   materials are consumable/counted, inventory needs quantities (`dict[name, count]` or
   `list[(entity, qty)]`), whereas utensils are likely unique/non-consumable. that pressure points
   toward either a `kind` field on a unified `Item` (item|utensil|material) or two separate
   containers. crafting should also resolve against the catalogue rather than inventing entities.
4. **align utensil with the entity family**: make it a `BaseModel` and give it a type/instance
   split if utensils ever need per-instance state.
