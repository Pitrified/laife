# data_models

The shared pydantic base.
Source: [`src/laife/data_models/`](../../src/laife/data_models).

## BaseModelKwargs

[`basemodel_kwargs.py`](../../src/laife/data_models/basemodel_kwargs.py) re-exports `BaseModelKwargs` from `llm_core`.
The re-export keeps `laife` imports stable while the definition stays in one place upstream.

`BaseModelKwargs` is the base for config-like models that get forwarded as keyword arguments to third-party constructors, with a flattening helper for a nested kwargs dict.
The LLM chain input models in [the llm package](llm.md) extend it, which is how their fields come to define the required prompt variables.
