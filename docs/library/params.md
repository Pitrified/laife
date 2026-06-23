# params

Environment-aware settings for the project.
Source: [`src/laife/params/`](https://github.com/Pitrified/laife/tree/main/src/laife/params).
For the concepts and the secret-handling rules see [the params and config guide](../guides/params_config.md).

## Entry point

[`laife_params.py`](https://github.com/Pitrified/laife/blob/main/src/laife/params/laife_params.py) defines `LaifeParams`, the singleton that aggregates everything: paths and LLM service params.
It is constructed from an `EnvType` and shared process-wide.

## Environment

[`env_type.py`](https://github.com/Pitrified/laife/blob/main/src/laife/params/env_type.py) defines the stage and location enums and how they are read from environment variables.
This is the switch every other params class dispatches on.

## Paths

[`laife_paths.py`](https://github.com/Pitrified/laife/blob/main/src/laife/params/laife_paths.py) defines `LaifePaths`, which resolves filesystem locations per environment location.

## LLM services

[`llm_services/`](https://github.com/Pitrified/laife/tree/main/src/laife/params/llm_services) holds the per-service settings:

- [`chat.py`](https://github.com/Pitrified/laife/blob/main/src/laife/params/llm_services/chat.py) - chat model settings for the player and world chains.
- [`embeddings.py`](https://github.com/Pitrified/laife/blob/main/src/laife/params/llm_services/embeddings.py) - embedding model settings.
- [`search.py`](https://github.com/Pitrified/laife/blob/main/src/laife/params/llm_services/search.py) - vector search settings, which build on the embeddings.

`LLMServicesParams` in [`__init__.py`](https://github.com/Pitrified/laife/blob/main/src/laife/params/llm_services/__init__.py) assembles the three.

## Secrets

[`load_env.py`](https://github.com/Pitrified/laife/blob/main/src/laife/params/load_env.py) loads credentials from `~/cred/laife/.env`.
Secret values come only from the environment; non-secret values are written as literals selected per environment.
