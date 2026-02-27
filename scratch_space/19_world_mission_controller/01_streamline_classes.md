# Streamline chain classes

ActionPicker and WorldActionJudge share many commonalities

- chat config
- prompt str
- post init and chain building
- required prompt variables guard
- invoke and ainvoke methods

only change is the type of input and output models,
which we want to keep separate for type safety and clarity

also invoke and ainvoke are quite similar,
only the actual chain call is different

---

## Analysis

### What is duplicated today

| Element                          | `ActionPicker` (action.py)                                                                                                     | `WorldActionJudge` (world_judge.py)                      |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| Dataclass fields                 | `chat_config`, `prompt_str`                                                                                                    | identical                                                |
| `__post_init__`                  | build `ChatPromptTemplate`, check missing vars, `create_chat_model()`, `with_structured_output(ActionEnvelope)`, compose chain | identical except output model is `WorldJudgeResult`      |
| `_REQUIRED_PROMPT_VARS` sentinel | `frozenset(ActionPickerInput.model_fields)`                                                                                    | `frozenset(WorldJudgeInput.model_fields)` - same pattern |
| `MissingPromptVariablesError`    | copy-pasted verbatim                                                                                                           | copy-pasted verbatim                                     |
| `invoke` / `ainvoke`             | call `chain.invoke(input.to_kw())`, `isinstance` guard, raise `TypeError`, return `output.act`                                 | identical except returns `output` directly (no unwrap)   |

The only genuine differences are:

1. **Output model**: `ActionEnvelope` vs `WorldJudgeResult`
2. **Return value**: `ActionPicker` unwraps `output.act`; `WorldActionJudge` returns `output` as-is
3. **Input model** (determines required prompt variables): `ActionPickerInput` vs `WorldJudgeInput`

### Proposed solution: `StructuredLLMChain`

Extract all shared infrastructure into a new generic dataclass in `src/laife/llm/structured_chain.py`.
Pass `input_model` and `output_model` as constructor arguments so the chain is fully self-contained and the required-vars guard runs automatically.

```python
# src/laife/llm/structured_chain.py

@dataclass
class StructuredLLMChain[InputT: BaseModelKwargs, OutputT: BaseModel]:
    chat_config: ChatConfig
    prompt_str: str
    input_model: type[InputT]   # drives required_vars check
    output_model: type[OutputT] # passed to with_structured_output

    def __post_init__(self) -> None:
        # build ChatPromptTemplate, check missing vars, build chain - once, here

    def invoke(self, chain_input: InputT) -> OutputT: ...
    async def ainvoke(self, chain_input: InputT) -> OutputT: ...
```

`MissingPromptVariablesError` also moves here - it is not specific to either domain class.

### How ActionPicker and WorldActionJudge simplify

Both keep their public API unchanged (same field names, same method signatures) so callers need no changes.

**`ActionPicker`** - delegates to `StructuredLLMChain[ActionPickerInput, ActionEnvelope]` and unwraps `.act`:

```python
@dataclass
class ActionPicker:
    chat_config: ChatConfig
    prompt_str: str

    def __post_init__(self) -> None:
        self._chain: StructuredLLMChain[ActionPickerInput, ActionEnvelope] = StructuredLLMChain(
            chat_config=self.chat_config,
            prompt_str=self.prompt_str,
            input_model=ActionPickerInput,
            output_model=ActionEnvelope,
        )

    def invoke(self, action_input: ActionPickerInput) -> BaseAction:
        return self._chain.invoke(action_input).act

    async def ainvoke(self, action_input: ActionPickerInput) -> BaseAction:
        return (await self._chain.ainvoke(action_input)).act
```

**`WorldActionJudge`** - delegates to `StructuredLLMChain[WorldJudgeInput, WorldJudgeResult]` and returns directly:

```python
@dataclass
class WorldActionJudge:
    chat_config: ChatConfig
    prompt_str: str

    def __post_init__(self) -> None:
        self._chain: StructuredLLMChain[WorldJudgeInput, WorldJudgeResult] = StructuredLLMChain(
            chat_config=self.chat_config,
            prompt_str=self.prompt_str,
            input_model=WorldJudgeInput,
            output_model=WorldJudgeResult,
        )

    def invoke(self, judge_input: WorldJudgeInput) -> WorldJudgeResult:
        return self._chain.invoke(judge_input)

    async def ainvoke(self, judge_input: WorldJudgeInput) -> WorldJudgeResult:
        return await self._chain.ainvoke(judge_input)
```

### Files to create / modify

| File                                 | Change                                                                                                                         |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| `src/laife/llm/structured_chain.py`  | New - `StructuredLLMChain`, `MissingPromptVariablesError`                                                                      |
| `src/laife/entities/action.py`       | Remove `_REQUIRED_PROMPT_VARS`, `MissingPromptVariablesError`, `__post_init__` body; `ActionPicker` wraps `StructuredLLMChain` |
| `src/laife/entities/world_judge.py`  | Same removals; `WorldActionJudge` wraps `StructuredLLMChain`                                                                   |
| `tests/llm/test_structured_chain.py` | New - tests for `StructuredLLMChain` and `MissingPromptVariablesError`                                                         |
| `tests/entities/test_world_judge.py` | Update `MissingPromptVariablesError` import to `laife.llm.structured_chain`                                                    |
| `tests/llm/test_player_brain.py`     | Update `MissingPromptVariablesError` import if referenced                                                                      |

### What stays the same

- All public types and method signatures (`ActionPicker`, `WorldActionJudge`, their `invoke`/`ainvoke`)
- `ActionPickerInput`, `WorldJudgeInput`, `WorldJudgeResult` - domain types, each lives in its own module
- No callers (`PlayerBrain`, `WorldRunner`, existing tests) need to change
