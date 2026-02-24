# Analyze world render possibilities

should we split the world render from the world runner?
and similar, for players, should we split the player sprite from the player runner?

---

## Analysis Report

### 1. Current State of the Codebase

#### 1.1 `World` class (`src/laife/entities/world.py`)

`World` currently owns two fully distinct responsibilities that are interleaved within a single class:

**Simulation / runner responsibilities:**

- `simulate()` - the main async loop that processes player requests from the queue
- `handle_player_input()` / `add_player()` / `add_building()` - world state mutation
- `self.players` and `self.buildings` (`pygame.sprite.Group`) - entity state storage
- `move_player()` / `craft()` - stub game logic

**Renderer responsibilities:**

- `init_renderer()` - calls `pygame.init()`, `pygame.display.set_mode()`, creates the display window
- `render()` - async loop (spawned as a task in `__init__`) that drives the visual update cycle
- `check_events()` - pygame event polling, including `pygame.QUIT` and `pygame.K_q`
- `quit()` - calls `pygame.quit()` and `sys.exit()`
- `redraw()` - fills screen black, calls `.draw()` on both sprite groups, flips the display
- `should_redraw()` / `reset_deadline()` - rate-limiting timer
- `self.screen`, `self.redraw_period_sec`, `self.redraw_deadline`, `self.render_task`

The render task is spawned inside `__init__` via `init_renderer()`, meaning a `World` instance is never just a simulation - it is always also a windowed pygame application.

#### 1.2 `Player` class (`src/laife/entities/player.py`)

`Player(Sprite)` inherits directly from `pygame.sprite.Sprite` and mixes agent logic with sprite management:

**Runner / agent responsibilities:**

- `play()` - async loop (task spawned in `__init__`) that drives the agent decision cycle
- `think()` - decides the next `Action` via `Brain`
- `move()` / `build()` / `craft()` / `plan()` - action handlers that communicate with the world via queues
- `world_request()` - sends `WReq` to the world and awaits a `WRes`
- `self.brain`, `self.mission`, `self.history`, `self.world_input_queue`, `self.input_queue`

**Sprite / renderer responsibilities:**

- `set_state()` - changes `self.state` enum AND immediately loads and sets `self.image` from the `SpriteLoader`
- `set_position()` - updates `self.position` AND mutates `self.rect.center` (pygame render rect)
- `self.sprite_loader` - a `SpriteLoader` instance that file-loads png assets
- `self.image` / `self.rect` - required pygame `Sprite` contract, consumed by `Group.draw()`

State transitions (`set_state`) are called throughout the agent loop (e.g. before and after `think()`, `move()`) purely so the visual sprite reflects the agent's current activity. This means agent logic directly drives the rendering data.

#### 1.3 `Building` class (`src/laife/entities/building.py`)

`Building(Sprite)` has a similar, but smaller, dual-concern: it creates a real pygame surface (`create_sprite()`) at construction time, blending entity data with visual rendering. However its rendering concern is more self-contained - the surface is created once and not mutated by game logic.

---

### 2. Key Problems with the Current Design

#### 2.1 Impossibility of headless simulation

`World.__init__` unconditionally calls `pygame.init()` and `pygame.display.set_mode()`. There is no way to instantiate the world without opening a display window. This blocks:

- Unit and integration testing of game logic
- LLM agent training / batch simulation runs
- Server-side or CI execution

The same applies to `Player` - `set_state()` calls `self.sprite_loader.load_sprite()` which calls `pygame.image.load()`, which requires pygame to be initialized with a display.

#### 2.2 Tight coupling between state change and visual update

`set_state()` in `Player` conflates two operations: updating the logical state enum and reloading the sprite image. This makes it impossible to change the player's logical state without touching pygame surfaces, and impossible to update the sprite without going through the state transition method.

#### 2.3 Rendering is load-bearing for game logic

`self.players` and `self.buildings` are `pygame.sprite.Group` instances. They are used both for collision detection (`pygame.sprite.spritecollideany`) and for rendering (`group.draw(screen)`). This is a subtle but important coupling: the rendering data structure is the authoritative game-logic data structure.

#### 2.4 Lifecycle coupling

Both the render loop (`World.render_task`) and the agent loop (`Player.play_task`) are spawned as asyncio tasks inside `__init__`. Starting a `World` or `Player` object immediately starts coroutines. There is no clean separation between instantiation and activation, and no mechanism to start a `Player` without also starting its visual update cycle.

#### 2.5 Untestable agent logic

No test in `tests/` covers `World` or `Player` behavior. The tight coupling to pygame is the main blocker - any test that instantiates these classes needs a display server.

---

### 3. Proposed Split

#### 3.1 World: `WorldRunner` + `WorldRenderer`

```
WorldRunner
  ├── entities: list[PlayerAgent]  (pure position + state data)
  ├── buildings: list[BuildingData]
  ├── simulate()
  ├── handle_player_input()
  ├── add_player() / add_building()
  └── collision_check()  (geometry-based, no pygame needed)

WorldRenderer
  ├── runner: WorldRunner  (read reference)
  ├── screen: pygame.Surface
  ├── player_sprites: dict[PlayerAgent, PlayerSprite]
  ├── building_sprites: dict[BuildingData, BuildingSprite]
  ├── render()   ← async loop
  ├── check_events()
  ├── redraw()
  └── quit()
```

`WorldRenderer` holds references to `WorldRunner` state and maintains its own sprite dictionary. The runner never imports pygame. The renderer is the only component that calls `pygame.init()`.

Collision detection can be moved to pure geometry (axis-aligned bounding box check on `Position` + `Size` tuples) inside `WorldRunner`, removing the dependency on `pygame.sprite.spritecollideany`.

#### 3.2 Player: `PlayerAgent` + `PlayerSprite`

```
PlayerAgent
  ├── name, position: Position, state: PlayerState
  ├── brain: Brain
  ├── mission: Mission
  ├── history: MissionHistory
  ├── world_input_queue: asyncio.Queue
  ├── play()   ← async loop (task created externally, not in __init__)
  ├── think() / move() / build() / craft() / plan()
  └── world_request()

PlayerSprite(pygame.sprite.Sprite)
  ├── agent: PlayerAgent  (read reference)
  ├── sprite_loader: SpriteLoader
  ├── sync()   ← called by renderer each frame: reads agent.state and agent.position, updates image/rect
  └── update()  ← pygame Sprite.update() hook
```

`PlayerAgent` becomes a plain Python object with no pygame dependency. `PlayerSprite` wraps it for rendering. `WorldRenderer` creates and owns the `PlayerSprite` objects; `WorldRunner` creates and owns `PlayerAgent` objects. State change in `PlayerAgent` does not immediately touch any surface - the renderer syncs on its next frame.

#### 3.3 Building: `BuildingData` + `BuildingSprite`

Same pattern as Player: `BuildingData` is a dataclass/pydantic model with `name`, `building_type`, `description`, `position`, `size`, and `to_prompt()`. `BuildingSprite` owns `create_sprite()` and the pygame surface.

---

### 4. Migration Considerations

| Concern                   | Current                               | After split                                     |
| ------------------------- | ------------------------------------- | ----------------------------------------------- |
| Collision detection       | `pygame.sprite.spritecollideany`      | Pure AABB geometry function                     |
| Sprite group draw         | `Group.draw(screen)` on shared groups | Renderer iterates its own sprite list           |
| State transition → visual | `set_state()` does both               | `agent.state = ...` then renderer syncs         |
| Task lifecycle            | Tasks spawned in `__init__`           | Tasks spawned explicitly by a coordinator       |
| Testing                   | Requires display server               | Runner logic fully testable headless            |
| Headless simulation       | Impossible                            | `WorldRunner` + `PlayerAgent` only, no renderer |

#### 4.1 The sprite group collision problem

`pygame.sprite.spritecollideany(building, self.buildings)` requires both sides to have a `.rect`. If `Building` becomes a dataclass, this call breaks. The replacement is a pure function:

```python
def aabb_collides(pos_a: Position, size_a: Size, pos_b: Position, size_b: Size) -> bool:
    ax1, ay1 = pos_a
    ax2, ay2 = ax1 + size_a[0], ay1 + size_a[1]
    bx1, by1 = pos_b
    bx2, by2 = bx1 + size_b[0], by1 + size_b[1]
    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1
```

This is straightforward since all buildings are rectangular and positions are top-left corners (matching `.rect.topleft = self.position` in the current `Building.create_sprite()`).

#### 4.2 Renderer sync strategy

Two valid approaches:

- **Pull (recommended)**: Renderer reads `agent.state` and `agent.position` each frame in `PlayerSprite.sync()`. No coupling back from agent to renderer.
- **Push (event-driven)**: `PlayerAgent` emits events (e.g. via a small observable or asyncio event) on state change. Renderer subscribes. More responsive but adds complexity.

The pull approach is simpler and sufficient given the current 100ms render tick (`asyncio.sleep(0.1)` in `World.render()`).

#### 4.3 Task lifecycle

A dedicated `GameCoordinator` or the top-level `main()` in `game/main.py` should own task creation:

```python
async def main():
    runner = WorldRunner()
    renderer = WorldRenderer(runner)

    setup_world(runner)

    await asyncio.gather(
        runner.simulate(),
        renderer.render(),
        *[agent.play() for agent in runner.agents],
    )
```

This makes it explicit which coroutines are running and allows individual components to be started or omitted (e.g. skip `renderer.render()` for headless mode).

---

### 5. Verdict

**Yes, the split is well-justified and the codebase is in a good position to do it.**

The mixing of rendering and logic is already causing practical problems (no tests for world/player logic exist) and will become a hard blocker for the LLM agent development path (training, batch simulation, deterministic replay). The split is not a premature abstraction - it aligns exactly with the two independently evolving axes of this project: the AI/agent behavior layer and the pygame visualization layer.

The `Building` class is the easiest to split and would be a good starting point. The `Player` split is the highest-value item since it unblocks testing of the agent loop. The `World` split follows naturally once `Player` is clean.

The `scratch_space/game/world_loop.py` prototype actually pre-figures this architecture in its own way - `SpriteLoader` is already a standalone class separate from `Player` logic - which validates the direction.
