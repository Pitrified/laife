# Getting started

How to set up `lAIfe` locally and run it.
This page summarizes the setup; [CONTRIBUTING](https://github.com/Pitrified/laife/blob/main/CONTRIBUTING.md) owns the full instructions and the system packages needed for pygame.

## Install

The project uses `uv` for dependency management and targets Python 3.14.

```bash
uv sync --all-extras --all-groups
```

Pygame needs SDL2 development libraries on the host.
If `uv sync` fails on the SDL2 build, install them as described in [CONTRIBUTING](https://github.com/Pitrified/laife/blob/main/CONTRIBUTING.md).

## Credentials

LLM and embedding calls need API keys.
Place them in `~/cred/laife/.env`; the required keys are listed in [`nokeys.env`](https://github.com/Pitrified/laife/blob/main/nokeys.env).
They are loaded by `load_env` in [`src/laife/params/load_env.py`](https://github.com/Pitrified/laife/blob/main/src/laife/params/load_env.py).

## Run the game

```bash
uv run python game/main.py
```

A pygame window opens with the world, the players, and the buildings.
Press `q` to quit.
The entry point [`game/main.py`](https://github.com/Pitrified/laife/blob/main/game/main.py) shows how the world is assembled; see [the architecture guide](architecture.md) for what each piece does.

## Checks

The standard verification suite for the linux-box ecosystem:

```bash
uv run pytest
uv run ruff check .
uv run pyright
```

## Makefile shortcuts

A `Makefile` wraps the common commands.
Run `make help` to list every target.

```bash
make sync          # install all dependencies (extras and groups)
make run           # run the game
make test          # run tests
make lint          # lint with ruff
make format        # format with ruff
make typecheck     # type-check with pyright
make docs          # serve the docs locally with MkDocs
make dev-llm-core  # install llm-core from a local editable path
```
