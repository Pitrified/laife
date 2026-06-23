# `lAIfe`

<!-- never edit the following line -->
Fully unscripted life simulation.
<!-- edit the rest -->

`lAIfe` is a sandbox where LLM-driven players live in a 2D world.
Each player observes what is around it, thinks about a mission, and asks the world to act.
The world is the only authority: it validates every request, runs collision and judging, and answers with a typed response.
Nothing is scripted; missions, plans, and conversations all emerge from the LLM calls.

For the game pitch and the running list of ideas and features see the [project README](https://github.com/Pitrified/laife/blob/main/README.md).
For local setup see [CONTRIBUTING](https://github.com/Pitrified/laife/blob/main/CONTRIBUTING.md).

## Documentation map

The docs are split in two trees.

- [`guides/`](guides/README.md) - cross-cutting explanations: how to run the game, the overall architecture, the game loop, the LLM chains, and configuration.
- [`library/`](library/README.md) - one page per source module under [`src/laife/`](https://github.com/Pitrified/laife/tree/main/src/laife), describing what each module is for and linking to the code.

## Start here

- New to the project: read [getting started](guides/getting_started.md), then [architecture](guides/architecture.md).
- Want to follow a single turn end to end: read [the game loop](guides/game_loop.md).
- Working on prompts or LLM behavior: read [LLM chains](guides/llm_chains.md).
- Changing environments, paths, or model providers: read [params and config](guides/params_config.md).
- Unsure what a term means: check [the glossary](guides/glossary.md).

## Build and serve locally

The site is built with MkDocs and the Material theme;
the API reference under `reference/` is generated from the source docstrings, so it is never written by hand.

Install the docs tooling and start a live-reloading server:

```bash
uv sync --only-group docs
uv run mkdocs serve
```

The server prints a local URL, usually `http://127.0.0.1:8000`, and rebuilds on save.
To produce the static site once, with the same strict checks as CI:

```bash
uv run mkdocs build --strict
```

Pushing to `main` publishes the site to GitHub Pages through [the docs workflow](https://github.com/Pitrified/laife/blob/main/.github/workflows/docs.yml).

## Conventions

All docs follow [the docs standards](standards.md).
The code follows the conventions in the repo [Copilot instructions](https://github.com/Pitrified/laife/blob/main/.github/copilot-instructions.md).
