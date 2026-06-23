# config

Type aliases and project-level constants.
Source: [`src/laife/config/`](../../src/laife/config).

## Types

[`types.py`](../../src/laife/config/types.py) defines `Position` and `Size` as integer tuples compatible with `pygame.Rect`.
Using these aliases keeps the logic and rendering layers speaking the same coordinate language.

[`types.py`](../../src/laife/config/types.py) holds only aliases; richer settings models can be added here as the project grows.

## Constants

[`constants.py`](../../src/laife/config/constants.py) holds fixed filesystem locations and names that do not depend on the environment: the static, sprites, cache, and data folders, the LangChain cache path, the vector store location, and collection names.
Environment-dependent paths live in [the params package](params.md) instead.
