# Getting started

How to set up `lAIfe` locally and run it.
This page summarizes the setup; [CONTRIBUTING](https://github.com/Pitrified/laife/blob/main/CONTRIBUTING.md) owns the full instructions.

## Install

The project uses `uv` for dependency management and targets Python 3.14.

```bash
uv sync --all-extras --all-groups
```


## Credentials

LLM and embedding calls need API keys.
Place them in `~/cred/laife/.env`; the required keys are listed in [`nokeys.env`](https://github.com/Pitrified/laife/blob/main/nokeys.env).
They are loaded by `load_env` in [`src/laife/params/load_env.py`](https://github.com/Pitrified/laife/blob/main/src/laife/params/load_env.py).

## Run the game

```bash
make vendor   # once: the page's third-party JavaScript
make run      # 3 turns per player, served on http://127.0.0.1:8002, paused
```

Open the page and press resume: every player turn calls the provider and spends credit, so the run starts paused and stops after `LIVE_TURNS` turns per player (`LIVE_TURNS=0` for no limit).
Quit from the page, or Ctrl-C.
The entry point [`game/main.py`](https://github.com/Pitrified/laife/blob/main/game/main.py) starts the pieces; the starting world is built in [`world_setup.py`](https://github.com/Pitrified/laife/blob/main/src/laife/entities/world_setup.py). See [the architecture guide](architecture.md) for what each piece does.

To run with no provider, see [Headless run](headless.md); `make headless SERVE=1` serves it on the same page. See [Serving the world](web.md) for the page and its options.

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
make run           # play the live game on the page (calls the provider)
make test          # run tests
make vendor        # fetch the page's third-party JavaScript into cache/vendor/
make e2e           # browser tests of the world page (not part of make check)
make lint          # lint with ruff
make format        # format with ruff
make typecheck     # type-check with pyright
make docs          # serve the docs locally with MkDocs
make dev-llm-core  # install llm-core from a local editable path
```
