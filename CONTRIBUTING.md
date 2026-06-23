# Contributing

## Setup local development environment

### Pygame

might need SDL to solve this error:

`RuntimeError: Unable to run "sdl-config". Please make sure a development version of SDL is installed.`

which actually need SDL2

```
sudo apt install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    libjpeg-dev \
    libpng-dev
```

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
