# Contributing

## Setup local development environment

### Pygame

might need SDL to solve

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
poetry install
```

edit the chromadb package to deal with the old sqlite3 version

`~/.cache/pypoetry/virtualenvs/laife-IdkopDz3-py3.11/lib/python3.11/site-packages/chromadb/__init__.py`

around line 86 where the import fails

```
            __import__("pysqlite3")
            import sys
            sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
```

### Openai key

place the openai key in `src/laife/config/credentials.py`:

```python
from pydantic.v1 import SecretStr

OPENAI_API_KEY = SecretStr("your-openai-api-key")
```

### Run the game

```bash
poetry run python game/main.py
```