# Dataclass check

we use dataclass and pydantic models

why do we use them both? can we unify the approach, possibly using pydantic models everywhere?

---

## Current usage

### Dataclasses

| File                   | Class          | Nature                                                                                                            |
| ---------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------- |
| `entities/action.py`   | `ActionPicker` | **Service/logic object** - owns a LangChain chain, validates prompt template in `__post_init__`, builds LLM chain |
| `entities/building.py` | `Building`     | **Game-state entity** - holds position/size (plain tuples), has display/prompt methods                            |
| `llm/prompt_loader.py` | `PromptLoader` | **Service/logic object** - loads/caches a jinja file from disk                                                    |
| `params/env_type.py`   | `EnvType`      | **Tiny value object** - holds two enums, has a `from_env_var` factory                                             |

### Pydantic BaseModel / BaseModelKwargs

| File                          | Class                                                                                    | Nature                                                                      |
| ----------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `entities/action.py`          | `BaseAction`, `ActionMove`, `ActionBuild`, `ActionCraft`, `ActionPlan`, `ActionEnvelope` | **LLM structured-output schemas** - required by `.with_structured_output()` |
| `entities/action.py`          | `ActionPickerInput`                                                                      | **Payload object** - uses `to_kw()` from `BaseModelKwargs`                  |
| `llm/prompt_loader.py`        | `PromptLoaderConfig`                                                                     | **Config value object** - validated, `Path` coercion                        |
| `llm/player_brain.py`         | `PlayerBrainConfig`                                                                      | **Config value object**                                                     |
| `llm_services/**/config/*.py` | `ChatConfig`, `EmbeddingsConfig`, subclasses                                             | **Config value objects**                                                    |

---

## Can we unify to pydantic everywhere?

**Short answer: yes for value objects, no/not recommended for the service classes.**

### Migrate to pydantic (easy wins)

- **`EnvType`** - pure data, two enum fields, a factory classmethod. `from_env_var` as a `@classmethod` on `BaseModel` is fully supported. Free validation, no friction.
- **`Building`** - pure data + display/prompt methods, no mutable state beyond construction. Pydantic adds field validation. `description: str | None = field(default=None)` becomes `description: str | None = Field(default=None)`.

### Keep as dataclass

- **`ActionPicker`** - a **service**, not a data container. Builds a LangChain chain in `__post_init__`, stores mutable derived state (`self.chain`, `self.structured_llm`, `self.model`). Pydantic can technically model this with `model_config = ConfigDict(arbitrary_types_allowed=True)` and `model_post_init`, but it adds complexity for no gain. Dataclass is the right tool for a stateful worker.
- **`PromptLoader`** - same reasoning: service class with a private cache field (`_prompt_cache`, `init=False, repr=False`). Pydantic `PrivateAttr` can replicate this but is more boilerplate.

---

## Verdict

The split is already semantically clean: **data/config → pydantic, service/logic → dataclass**. All `*Config` classes are already pydantic. Only two classes are outliers and could be migrated:

| Class          | Recommended action     |
| -------------- | ---------------------- |
| `EnvType`      | Migrate to `BaseModel` |
| `Building`     | Migrate to `BaseModel` |
| `ActionPicker` | Keep as `@dataclass`   |
| `PromptLoader` | Keep as `@dataclass`   |
