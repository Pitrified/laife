# Contributing

## Setup local development environment

### Install package

```bash
make sync
```

### API key

place the API keys in `~/cred/laife/.env`, refer to `nokeys.env` for required keys.

### Run the game

```bash
make run
```

### Run tests, lint, type-check

```bash
make test       # run tests
make lint       # lint with ruff (ALL rules enabled - see ruff.toml)
make typecheck  # type-check with pyright (src/ and tests/ only)
```

Run `make help` to list every available target.
