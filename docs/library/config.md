# config

Type aliases and project-level constants.
Source: [`src/laife/config/`](https://github.com/Pitrified/laife/tree/main/src/laife/config).

## Types

[`types.py`](https://github.com/Pitrified/laife/blob/main/src/laife/config/types.py) defines `Position` and `Size` as integer tuples in world pixels: a rectangle is its top-left corner and its size, and y grows South.
The page draws in the same coordinates, so the logic and the view agree on where things are.

[`types.py`](https://github.com/Pitrified/laife/blob/main/src/laife/config/types.py) holds only aliases; richer settings models can be added here as the project grows.

## Constants

[`constants.py`](https://github.com/Pitrified/laife/blob/main/src/laife/config/constants.py) holds fixed filesystem locations and names that do not depend on the environment: the static, sprites, cache, and data folders, the LangChain cache path, the vector store location, and collection names.
Environment-dependent paths live in [the params package](params.md) instead.
