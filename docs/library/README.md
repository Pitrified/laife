# Library

High-level documentation for the code under [`src/laife/`](https://github.com/Pitrified/laife/tree/main/src/laife).
Each page mirrors one package and links to the source files for detail.
For cross-cutting explanations see [the guides](../guides/README.md).

## Packages

- [entities](entities.md) - the world, players, buildings, terrain, utensils, actions, and the world channel.
- [llm](llm.md) - the player brain, planner, replier, mission generator, and the mission model.
- [prompts](prompts.md) - the versioned Jinja templates that drive the LLM chains.
- [rendering](rendering.md) - the pygame view layer and sprites.
- [web](web.md) - the world served over HTTP: snapshot, event stream, pause controls.
- [params](params.md) - environment-aware settings, paths, and LLM service params.
- [config](config.md) - type aliases and project-level constants.
- [meta](meta.md) - the structured logger.
- [ui](ui.md) - the asynchronous console logger.

## How the packages relate

The pure logic lives in `entities`, `llm` and `config`, with no pygame dependency.
`prompts` holds the template text the `llm` chains load at runtime.
`rendering`, `web` and `ui` are presentation layers that observe the logic; `web` also drives the pause control.
`params` and `config` supply settings to all of them.
`meta` holds support utilities.
See [the architecture guide](../guides/architecture.md) for the runtime picture.
