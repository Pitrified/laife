# Split the modules in cleaner sub-folders

we have three main folders for core game running and LLM logic:

- llm
- entities
- ui

please analyze the content of these folders and propose a reorganization of the existing modules
eg player_sparite is related to ui, player_agent is related to entities (no UI)
brain (which is a player brain) is related to LLM

---

## Analysis

### Current state - module responsibilities

| Module               | Location    | pygame? | LLM?         | Verdict         |
| -------------------- | ----------- | ------- | ------------ | --------------- |
| `action.py`          | `entities/` | no      | prompts only | ✅ entities     |
| `building_data.py`   | `entities/` | no      | no           | ✅ entities     |
| `geometry.py`        | `entities/` | no      | no           | ✅ entities     |
| `player_agent.py`    | `entities/` | no      | no           | ✅ entities     |
| `player_state.py`    | `entities/` | no      | no           | ✅ entities     |
| `utensil.py`         | `entities/` | no      | chroma       | ✅ entities     |
| `world_channel.py`   | `entities/` | no      | no           | ✅ entities     |
| `world_runner.py`    | `entities/` | no      | no           | ✅ entities     |
| `building_sprite.py` | `entities/` | **yes** | no           | ❌ wrong folder |
| `player_sprite.py`   | `entities/` | **yes** | no           | ❌ wrong folder |
| `world_renderer.py`  | `entities/` | **yes** | no           | ❌ wrong folder |
| `sprites.py`         | `ui/`       | **yes** | no           | ❌ wrong folder |
| `alog.py`            | `ui/`       | no      | no           | ✅ ui           |
| `directions.py`      | `ui/`       | no      | no           | ✅ ui           |
| `brain.py`           | `llm/`      | no      | **yes**      | ✅ llm          |
| `mission.py`         | `llm/`      | no      | **yes**      | ✅ llm          |

The core problem: `entities/` currently mixes pure game-state modules with pygame rendering modules.
`ui/` similarly mixes a pygame asset loader (`sprites.py`) with generic app utilities.

---

## Proposed structure

```
src/laife/
  entities/              ← pure game state + simulation - no pygame
    __init__.py
    action.py
    building_data.py
    geometry.py
    player_agent.py
    player_state.py
    utensil.py
    world_channel.py
    world_runner.py

  rendering/             ← NEW: all pygame-dependent code in one place
    __init__.py
    sprites.py           ← moved from ui/
    building_sprite.py   ← moved from entities/
    player_sprite.py     ← moved from entities/
    world_renderer.py    ← moved from entities/

  llm/                   ← unchanged
    __init__.py
    brain.py
    mission.py

  ui/                    ← non-pygame app utilities only
    __init__.py
    alog.py
    directions.py
```

### Rationale

**`rendering/` new package** - groups every file that `import pygame`. Only `WorldRenderer.__init__` ever calls `pygame.init()`. Having a dedicated package makes that boundary explicit and makes it trivial to exclude the whole package from headless / test environments.

**`entities/` shrinks** - three sprite files leave, making the invariant clear: nothing in `entities/` imports pygame.

**`ui/` shrinks** - `sprites.py` (SpriteLoader) is not a UI utility, it is a pygame asset-loading service consumed exclusively by the two sprite classes. Moving it to `rendering/` collapses the dependency naturally.

**`llm/` unchanged** - already clean.

### Import ripple

| File that moves      | Old import path                  | New import path                   |
| -------------------- | -------------------------------- | --------------------------------- |
| `sprites.py`         | `laife.ui.sprites`               | `laife.rendering.sprites`         |
| `building_sprite.py` | `laife.entities.building_sprite` | `laife.rendering.building_sprite` |
| `player_sprite.py`   | `laife.entities.player_sprite`   | `laife.rendering.player_sprite`   |
| `world_renderer.py`  | `laife.entities.world_renderer`  | `laife.rendering.world_renderer`  |

Callers affected:

- `src/laife/entities/__init__.py` - re-exports `BuildingSprite`, `PlayerSprite`, `WorldRenderer`
- `game/main.py` - imports `WorldRenderer`
- `src/laife/rendering/world_renderer.py` (internal) - imports `PlayerSprite`, `BuildingSprite`
- `src/laife/rendering/building_sprite.py` (internal) - imports `SpriteLoader` from `sprites`
- `src/laife/rendering/player_sprite.py` (internal) - imports `SpriteLoader` from `sprites`

All other modules (`world_runner`, `player_agent`, `building_data`, `llm/*`) have zero import changes.

---

## Additional considerations

### 1. Rename `PlayerAgent` → `Player`

**Verdict: ✅ yes, do it.**

The `Agent` suffix was a migration artifact introduced to avoid a name clash with the old combined `Player` shim class. That shim is now gone. In the split architecture the two roles are unambiguous by type alone: `Player` is the agent, `PlayerSprite` is its visual twin - exactly as the `Building` / `BuildingSprite` pair names things.

Keeping `PlayerAgent` carries a hidden cost: every caller that reads `list[PlayerAgent]`, `add_player(agent: PlayerAgent)`, or `f"PlayerAgent {self.name}"` pays a cognitive tax on a suffix that no longer signals anything distinct. The word "agent" is meaningful in the LLM domain (`Brain`, `Mission`) but at the entity level the object is simply a _player_.

**Impact:** `player_agent.py` → `player.py`, class renamed throughout. `WorldRunner.agents` could be renamed `WorldRunner.players` for consistency. Moderate but mechanical ripple confined to ~6 files.

**Note on symmetry with `BuildingData`:** `BuildingData` was not renamed `Building` after the split. Consider renaming it too for consistency, but that is a separate decision.
USER: please analyze and do it in this renaming step.

---

### 2. Merge `PlayerState` into `player.py`

**Verdict: ✅ yes, do it.**

`PlayerState` has exactly one semantic owner: the player entity. It is an internal implementation detail that controls both the agent's behaviour transitions and the sprite's frame selection. Giving it its own file implies it is a standalone, reusable concept - it is not.

Current consumers outside `player_agent.py` itself: `player_sprite.py` (rendering - reads `agent.state` for frame sync) and `entities/__init__.py` (re-export). Both would simply import `PlayerState` from `laife.entities.player` instead of `laife.entities.player_state`, which is more intuitive. The type is discovered naturally alongside the class that owns it.

**Impact:** delete `player_state.py`, move the 8-line enum to the top of `player.py`. Update 3 import sites. No logic changes.

---

### 3. Move `alog.py` to `rendering/`

**Verdict: ❌ no, do not do it.**

`Alog` is a headless async terminal logger. It has zero pygame dependency. Its consumers are:

| Consumer             | Package      | pygame? |
| -------------------- | ------------ | ------- |
| `player_agent.py`    | `entities/`  | no      |
| `world_runner.py`    | `entities/`  | no      |
| `world_renderer.py`  | `rendering/` | yes     |
| `building_sprite.py` | `rendering/` | yes     |
| `brain.py`           | `llm/`       | no      |
| `main.py`            | `game/`      | yes     |

Moving `alog` to `rendering/` would force the pure headless packages (`entities/`, `llm/`) to import from a package whose entire purpose is "pygame display code". That is the opposite direction of the separation we just established. The `rendering/` boundary would be breached by its own logging dependency.

`alog.py` belongs in `ui/` - stdout/terminal output is a legitimate UI concern - or in a dedicated `utils/` package if more general utilities accumulate. It does **not** belong in `rendering/`.

---

### 4. Move `directions.py` to `entities/` (with optional `utils/` subfolder)

**Verdict: ✅ yes, move to `entities/`; ⚠️ subfolder is optional.**

`directions.py` provides `CardinalDirection` and two pure math functions `pospos2cardinal_direction` / `pospos2cardinal_degrees`. It has no pygame dependency. Its only three production consumers are `action.py`, `building_data.py`, and `player_agent.py` - all in `entities/`. It was placed in `ui/` presumably because direction display in text form felt "UI-like", but spatial coordinate arithmetic is a game-model concern, not a rendering or presentation concern.

Moving to `entities/directions.py` (flat) is the minimal, clean change. The current test at `tests/ui/test_directions.py` moves to `tests/entities/test_directions.py`.

The `entities/utils/` subfolder idea pairs naturally with `geometry.py` (already in `entities/`), creating a clean sub-namespace for pure spatial helpers:

```
entities/
  utils/
    __init__.py
    directions.py   ← moved from ui/
    geometry.py     ← moved from entities/ root
```

This is worth doing if the project expects more spatial utilities to accumulate (e.g. pathfinding heuristics, grid snapping). If not, the subfolder is premature structure - a flat `entities/directions.py` is sufficient and avoids an extra `__init__.py` and import depth.
USER: please create the subfolder and move geometry.py in it as well
