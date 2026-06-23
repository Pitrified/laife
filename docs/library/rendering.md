# rendering

The pygame view layer.
Source: [`src/laife/rendering/`](../../src/laife/rendering).
Rendering observes the world; it never mutates it, so the simulation runs the same with or without a window.

## Renderer

[`world_renderer.py`](../../src/laife/rendering/world_renderer.py) defines `WorldRenderer`.
It reads the [`WorldRunner`](entities.md) state each frame and draws terrain, buildings, and players.
Terrain regions are filled with a color per terrain type.
The renderer initializes pygame, so it must be created before any sprite is loaded.

## Sprites

- [`sprites.py`](../../src/laife/rendering/sprites.py) - loads sprite sheets and slices the frames.
- [`player_sprite.py`](../../src/laife/rendering/player_sprite.py) - the player's drawable, reflecting position and state.
- [`building_sprite.py`](../../src/laife/rendering/building_sprite.py) - the building's drawable.

Positions and sizes use the pygame-compatible aliases from [the config package](config.md).
