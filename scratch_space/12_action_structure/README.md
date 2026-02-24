# Action structure clean up

## Original idea

In [src/laife/entities/action.py](../../src/laife/entities/action.py) we have a weird pattern of `Actions`
as a union, then `Action` that takes an `act` and a wrapper for a `reason`.

Can we instead define a base `Action` class, and then have specific action types inherit from it?

We can then pattern match like we do now at [player.py line 77](../../src/laife/entities/player.py#L77).

Can we also use that with a
`self.structured_llm = self.model.with_structured_output(Action)`
to get structured output from the LLM directly into our Action classes?

---

## Deep dive

### What makes sense

**Inheritance over composition for the type hierarchy.**
The current wrapper pattern forces a two-level indirection: you hold an `Action`, then reach into
`action.act` to get the real type. Inheritance removes that layer. `reason` moves to a base class,
each concrete type only carries its own payload, and callers deal with the concrete type directly.
The `get_action_*` extractor methods on `Action` become unnecessary.

**Pattern matching is a natural fit.**
Python's structural pattern matching works cleanly on a class hierarchy:

```python
match action:
    case ActionMove():  ...
    case ActionBuild(): ...
```

This reads well and Pyright/mypy can narrow types correctly in each branch.

---

### What was already broken (now fixed)

**The pattern match in `player.py` was matching against the wrapper, not the inner type.**
The match cases were `ActionMove()`, `ActionBuild()`, etc., but `action` was always of type
`Action` (the wrapper), so every branch fell through to `case _: action_handler = self.action_error`.
Fixed by matching on `action.act` instead. The inheritance refactor will eliminate this tension
entirely by making the returned value be the concrete type directly.

**`ActionPlan` had a duplicate `reason` field.**
`ActionPlan.reason` ("What is not clear?") shadowed `Action.reason` ("The reason for the action.").
This is already resolved: `ActionPlan` now drops its own `reason` and inherits the base one.

---

### What doesn't quite work as stated

**`with_structured_output(BaseAction)` won't produce subclasses.**
If `Action` becomes a plain base class with no union field, calling
`model.with_structured_output(Action)` gives the LLM a schema that only contains the base fields
(`reason`). It has no way to know about `direction`, `distance`, `building_type`, etc.

The current `ActionPicker` (which already exists in `action.py`) actually works correctly because
`Action.act` is typed as `Actions = ActionMove | ActionBuild | ActionCraft | ActionPlan` — that
union gets reflected in the JSON schema and the LLM can produce any of the four variants.

With inheritance the right target for `with_structured_output` is the **union of concrete types**,
not the base class:

```python
from typing import Union, Annotated
Actions = Annotated[
    Union[ActionMove, ActionBuild, ActionCraft, ActionPlan],
    Field(discriminator="type")
]
structured_llm = model.with_structured_output(Actions)
```

This requires a `type: Literal["move"]` discriminator field on each subclass so Pydantic (and the
LLM) can distinguish them unambiguously. The main unknown here is empirical: does the LLM reliably
produce the exact discriminator string, and does Pydantic route it to the correct class? A small
scratch notebook exercising `ActionPicker.invoke` against each action type is the right way to
validate before committing to this shape.

---

### Missed points

**`ActionPicker` already exists and already uses `with_structured_output`.**
The README describes `with_structured_output` as something to add, but `ActionPicker` in
`action.py` already wires it up. The missing step is connecting `Player.think()` to `ActionPicker`
— right now `think()` is hardcoded to return a fixed `ActionMove`. Wiring this up is deferred
until after the inheritance refactor is in place.

**`Brain` is completely disconnected from structured output.**
`Brain` (in [src/laife/llm/brain.py](../../src/laife/llm/brain.py)) uses `ChatOllama` with no
structured output and returns a raw string (`"move"` or `"rest"`). It is not integrated with
`ActionPicker` at all and is not used by `Player.think()` for action decisions. Full LLM wiring
for `Brain` is deferred.

**Handler signatures and the "store then call" dispatch pattern.**
The current pattern stores a handler in a variable then calls it once:

```python
match action:
    case ActionMove():
        action_handler = self.move
    case ActionBuild():
        action_handler = self.build
    ...
wrsp = await action_handler(action)
```

This is appealing because it avoids repeating `wrsp = await self.XXX(action)`. However it directly
conflicts with giving each handler a concrete type signature. The type checker must assign a single
type to `action_handler` — if handlers have different concrete parameter types, the call
`action_handler(action)` fails static analysis because `action` is `BaseAction`, not `ActionMove`.

The clean solution is to use pattern matching's `as` binding, which gives the narrowed concrete
type inside the branch at no extra cost:

```python
match action:
    case ActionMove() as act:
        wrsp = await self.move(act)
    case ActionBuild() as act:
        wrsp = await self.build(act)
    case ActionCraft() as act:
        wrsp = await self.craft(act)
    case ActionPlan() as act:
        wrsp = await self.plan(act)
    case _:
        wrsp = await self.action_error(action)
```

The repetition increases by one `wrsp = await` line per branch but each handler is fully typed,
the `get_action_*` extractors disappear, and static analysis works correctly throughout.
**Recommendation: inline the calls with `as` binding.**

**`ActionPicker.invoke` is synchronous; `Player.think` is async.**
Add an `async def ainvoke` method to `ActionPicker` that calls `self.chain.ainvoke(...)` and wire
`Player.think()` to it.

---

### `get_action_typed` — a middle path worth considering

A generic getter was added to `Action`:

```python
def get_action_typed(self, action_type: type[T]) -> T:
    if not isinstance(self.act, action_type):
        raise TypeError(f"Action is not of type {action_type.__name__}")
    return self.act
```

Called as `action.get_action_typed(ActionMove)`.

**What it does well:**

- Replaces the 4 specific `get_action_*` methods with one. Pyright correctly infers the return
  type as `T` (i.e. `ActionMove`) from the `type[T]` argument, so the caller gets full static
  narrowing — no cast needed.
- Useful in non-match contexts: loading actions from history, unit tests, or any code that holds
  an `Action` and already knows its type but isn't in a `match` branch.

**Where it is redundant:**
Inside a handler like `move(self, action: Action)`, calling `get_action_typed(ActionMove)` adds
a runtime `isinstance` check that the dispatch in `play()` already performed. The match branch
`case ActionMove():` already proved `action.act` is an `ActionMove` — `get_action_typed` just
re-asserts it inside the handler.

**`get_action_typed` vs `as` binding — they serve different callsites:**

| Context                             | Best tool                                                        |
| ----------------------------------- | ---------------------------------------------------------------- |
| Dispatch in `play()`                | `case ActionMove() as act:` — narrows statically, no extra check |
| Inside a handler receiving `Action` | `get_action_typed(ActionMove)` — re-establishes the type cleanly |
| Non-match code (history, tests)     | `get_action_typed(ActionMove)` — the only option without a match |

They are complementary. `as` binding in dispatch, `get_action_typed` inside handlers.

**Keeping handlers as `action: Action` vs narrowed types:**
Uniform `Action` input on all handlers has an underappreciated benefit: all handlers have the
same signature, which means they can be stored/called homogeneously if needed later. If handlers
take narrowed types (`action: ActionMove`), the dispatch must do the unwrapping before the call,
coupling the dispatch tightly to each handler's expected type. With uniform signatures the dispatch
stays simple and each handler is self-contained about what it expects.

---

### `BaseAction` with `reason` — reconsidered

If concrete classes inherit `reason: str` from a `BaseAction`, and `Action` (the LLM wrapper)
also has `reason: str`, the LLM schema would contain two `reason` fields: one at the outer
`Action` level and one inside each variant in `act`. The LLM would need to fill both, and they
would carry the same semantic meaning. That is confusing.

The clean options are:

**Option A — Drop `reason` from the wrapper, move it entirely to `BaseAction` and concrete classes.**
The LLM fills `reason` once, inside the chosen action. The wrapper becomes just `act: Actions`.
Handlers receive a `BaseAction` and have `reason` without going back to the wrapper. Clean, and
requires an intentional schema change + LLM prompt update.

**Option B — Keep `Action.reason`, `BaseAction` has no `reason`.**
`BaseAction` is just a marker for `isinstance` checks. Handlers that need `reason` read
`action.reason` from the wrapper. Essentially the status quo with a tag class added. Low benefit.

**Option C — Keep `Action.reason`, no `BaseAction` at all.**
Use `get_action_typed` for extraction and `as` binding in dispatch. Minimal change that removes
all the specific getters without touching the LLM boundary.

**Option A was implemented.** The clean long-term shape was worth the schema change.

---

### What the notebook revealed about the inheritance approach

The notebook (`discriminator_test.ipynb`) validated the discriminated union shape end-to-end.
Working through it surfaced two constraints:

1. **`with_structured_output` requires a `BaseModel` class with `type: "object"` at the root.**
   A discriminated union produces `anyOf`/`oneOf` at the root, which OpenAI rejects with a 400.
   The fix is to wrap it in an envelope model and use `method="function_calling"`. That envelope
   must live inside `ActionPicker` and be unwrapped before returning — callers never see it.

2. **The discriminator `type: Literal[...]` field adds fragility for no gain here.**
   Pydantic v2 can distinguish `ActionMove`, `ActionBuild`, etc. by field shape alone — no
   discriminator needed unless shapes overlap (ours don't). Adding it means the LLM must emit an
   extra field it can quietly omit, causing `union_tag_not_found` at parse time (observed in testing).
   **Leave it out.** Union routing by field shape works reliably.

---

### What was decided and implemented (Option A)

Option C (minimal change, keep wrapper) was the prior recommendation. After the notebook confirmed
the envelope constraint, **Option A was implemented instead** — `reason` was moved into `BaseAction`
and each concrete class inherits it, making the wrapper truly thin.

**Shape after the refactor:**

```python
class BaseAction(BaseModel):
    reason: str

class ActionMove(BaseAction):
    direction: Direction

class ActionBuild(BaseAction):
    building_type: BuildingType

class ActionCraft(BaseAction):
    item_name: str

class ActionPlan(BaseAction):
    next_actions: list[str]

Actions = ActionMove | ActionBuild | ActionCraft | ActionPlan

class ActionEnvelope(BaseModel):          # LLM boundary only — never leaves ActionPicker
    act: Actions

class ActionPicker:
    def invoke(self, mission: str) -> BaseAction:
        envelope: ActionEnvelope = self.chain.invoke(...)
        return envelope.act               # callers get a concrete BaseAction directly
```

**What this achieves over the old `Action(act, reason)` shape:**

- A handler that receives `ActionMove` has `reason` without needing to reach back to a wrapper.
- `isinstance(action, BaseAction)` works uniformly across all action types.
- The dispatch in `Player.play` matches directly on `action` (the returned `BaseAction`), not on
  `action.act`. Pattern match works as written.
- All handler signatures are `action: BaseAction` — uniform, easy to store and call.
- `ActionPlan` no longer duplicates a `reason` field (was always present on `ActionPlan` before).

**What it costs (known trade-offs):**

- The envelope is still required; it just lives entirely inside `ActionPicker`.
- No discriminator fields — clean, but means Pydantic routes the union by field shape. Add one
  only if two action types ever have identical field sets.

---

### Dispatch and type narrowing: `cast` vs `as` binding

Handlers currently use `cast()` to tell the type checker what the concrete type is:

```python
async def move(self, action: BaseAction) -> str:
    action = cast("ActionMove", action)   # type-checker hint only — no runtime check
    ...
```

`cast` is a lie: it does no validation. If the wrong action somehow reached the handler, it would
silently access wrong fields or raise an `AttributeError` at runtime with no clear cause.

The alternative is `as` binding at the dispatch site, which gives real narrowing (type checker
sees the concrete type; Python has already proven the isinstance):

```python
match action:
    case ActionMove() as act:
        wrsp = await self.move(act)       # act: ActionMove — type-safe, no cast needed
    case ActionBuild() as act:
        wrsp = await self.build(act)
    ...
```

This requires changing handler signatures from `BaseAction` to the concrete type, which breaks
the "store handler then call" pattern. The trade-off: a little more repetition at the call site,
but handlers that are honest about what they accept. **This is now implemented.** `cast` is gone;
all handlers take their concrete type; dispatch uses `as` binding throughout.

---

### Current implementation status

| Item                                                                    | Status                                       |
| ----------------------------------------------------------------------- | -------------------------------------------- |
| `BaseAction(reason)` with concrete classes inheriting                   | ✅ done                                      |
| `ActionEnvelope` as thin LLM-only wrapper, hidden inside `ActionPicker` | ✅ done                                      |
| `ActionPicker.invoke` returns `BaseAction`, uses `create_chat_model()`  | ✅ done                                      |
| `match action:` directly on concrete type in `Player.play`              | ✅ done                                      |
| Handlers accept `BaseAction` (uniform signatures)                       | ✅ done                                      |
| `get_action_*` specific extractors removed                              | ✅ done                                      |
| `ActionPlan.reason` duplication resolved (inherits from `BaseAction`)   | ✅ done                                      |
| Notebook validates all 4 types end-to-end with LLM                      | ✅ done                                      |
| `cast()` in handlers — unsafe, no runtime check                         | ✅ done — `as` binding + concrete signatures |
| `TypeVar T` import in `action.py` — dead code                           | ✅ done                                      |
| `ActionPicker.ainvoke` — async path                                     | ✅ done                                      |
| `Player.think()` wired to `ActionPicker`                                | ⏳ deferred — wiring goes through `brain`    |
| `Brain` wiring                                                          | ❌ deferred                                  |

---

### Remaining work

**Wire `Player.think()` through `Brain`**

The LLM call will live inside `Brain`, not be called directly via `ActionPicker` from `Player`.
`Brain` is still a stub returning a raw string and needs a full LLM wiring pass before
`think()` can be connected. Placeholder comment in `think()` reads:

```python
# > action = await self.brain.think(self.mission, self.history)
```

Once `Brain` is wired, `think()` becomes a one-liner delegating to it.
