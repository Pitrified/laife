# Params and config

How `lAIfe` loads settings and switches behavior between environments.
The modules are documented in [the params library page](../library/params.md) and [the config library page](../library/config.md).

## Environment type

Behavior is keyed on two axes defined in [`params/env_type.py`](../../src/laife/params/env_type.py):

- stage, dev or prod;
- location, where the code runs.

Both default from environment variables, `ENV_STAGE_TYPE` and `ENV_LOCATION_TYPE`, so the same code path adapts by reading the environment rather than branching on hardcoded flags.

## The params singleton

[`LaifeParams`](../../src/laife/params/laife_params.py) is the single entry point for project settings.
It is a singleton, built on the [`Singleton` metaclass](../library/meta.md), so the whole process shares one instance.
It aggregates the paths and the LLM service params, and is constructed from an `EnvType`.

Access it where you need settings rather than threading values through call signatures.

## Paths

[`LaifePaths`](../../src/laife/params/laife_paths.py) resolves filesystem locations and dispatches on the environment location.
Fixed, project-level locations that do not depend on the environment, such as the static and cache folders, live as constants in [`config/constants.py`](../../src/laife/config/constants.py).

## LLM services

[`LLMServicesParams`](../../src/laife/params/llm_services/__init__.py) holds the settings for the three LLM-facing services:

- chat, the models behind the brain, planner, replier, generator, and judge;
- embeddings, used to vectorize world entities;
- vector search, which uses the embeddings to retrieve relevant entities.

Each is loaded per environment, so swapping a model or provider is a params change, not a code change in the chains.

## Secrets

Secret values come only from the environment, loaded from `~/cred/laife/.env` by [`load_env`](../../src/laife/params/load_env.py).
Non-secret values are written as plain literals and selected by environment.
Keep secrets out of the config models and out of version control.
