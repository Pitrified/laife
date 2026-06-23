# Library

High-level documentation for the code under [`src/laife/`](https://github.com/Pitrified/laife/tree/main/src/laife).
Each page mirrors one package and links to the source files for detail.
For cross-cutting explanations see [the guides](../guides/README.md).

## Packages

- [entities](entities.md) - the world, players, buildings, terrain, utensils, actions, and the world channel.
- [llm](llm.md) - the player brain, planner, replier, mission generator, and the mission model.
- [prompts](prompts.md) - the versioned Jinja templates that drive the LLM chains.
- [rendering](rendering.md) - the pygame view layer and sprites.
- [params](params.md) - environment-aware settings, paths, and LLM service params.
- [config](config.md) - type aliases and project-level constants.
- [embed](embed.md) - the sentence-transformers embedding wrapper.
- [meta](meta.md) - the singleton metaclass and the structured logger.
- [ui](ui.md) - the asynchronous console logger.
- [data_models](data_models.md) - the shared pydantic base.

## How the packages relate

The pure logic lives in `entities`, `llm`, `config`, and `data_models`, with no pygame dependency.
`prompts` holds the template text the `llm` chains load at runtime.
`rendering` and `ui` are presentation layers that observe the logic.
`params` and `config` supply settings to all of them.
`meta` and `embed` are support utilities.
See [the architecture guide](../guides/architecture.md) for the runtime picture.
