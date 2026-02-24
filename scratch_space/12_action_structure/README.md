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

**Option A — Drop `reason` from `Action`, move it entirely to `BaseAction` and concrete classes.**
The LLM fills `reason` once, inside the chosen action. The wrapper becomes just `act: Actions`.
Handlers receive a `BaseAction` and have `reason` without going back to the wrapper. Clean, but
changes the LLM schema and removes the outer wrapper's most meaningful field.

**Option B — Keep `Action.reason`, `BaseAction` has no `reason`.**
`BaseAction` is just a marker for `isinstance` checks. Handlers that need `reason` read
`action.reason` from the wrapper. This is essentially the status quo with a tag class added.
Low benefit.

**Option C — Keep `Action.reason`, no `BaseAction` at all.**
Use `get_action_typed` for extraction and `as` binding in dispatch. This is the minimal change
that removes all the specific getters and keeps everything else intact.

Option A is the cleanest long-term shape but requires an intentional schema change. Option C is
the right short-term move: it delivers the cleanup without touching the LLM boundary.

---

### What the notebook revealed about the inheritance approach

The notebook (`discriminator_test.ipynb`) validated the discriminated union shape end-to-end.
Working through it surfaced two constraints that directly affect whether the full refactor is worth doing:

1. **`with_structured_output` requires a `BaseModel` class with `type: "object"` at the root.**
   A discriminated union produces `anyOf`/`oneOf` at the root, which OpenAI rejects. The fix was
   to wrap it in an `ActionEnvelope(action: Actions)` model and use `method="function_calling"`.
   That envelope is structurally identical to the existing `Action(act: Actions, reason: str)`.
   **The current wrapper is not a weird pattern — it is the required pattern for this LLM boundary.**

2. **The discriminator `type: Literal[...]` field adds fragility for no gain here.**
   Pydantic v2 can already distinguish `ActionMove`, `ActionBuild`, etc. by field shape (no
   discriminator needed). The `type` field is only required when shapes overlap. Since ours don't,
   adding it means the LLM must emit an extra field it has never been asked for, and can quietly
   omit it (observed during testing), causing a `union_tag_not_found` validation error.

---

### Is the shared base class worth it?

**Probably not as the primary refactor.** Here is the honest breakdown:

**What the inheritance refactor achieves:**

- `reason` lives on the concrete type, so a handler that receives `ActionMove` has everything it needs without reaching back to the wrapper.
- `isinstance(action, BaseAction)` works across all action types — useful for generic history/logging.
- Callers never see the wrapper; the dispatch and handler signatures are cleaner.

**What it costs:**

- `ActionPicker` still needs a `BaseModel` envelope for `with_structured_output` — the wrapper doesn't go away, it just moves inside `ActionPicker` and gets unwrapped before returning.
- Each concrete class needs a `reason` field that didn't exist before (or the envelope's `reason` must be copied into the concrete instance post-hoc, which is awkward with Pydantic's immutability).
- The `type` discriminator field is required if you want Pydantic to route the union cleanly, but adds LLM-side fragility.
- Net effect: the same complexity, just relocated.

**What already works fine:**
The existing `Action(act: Actions, reason: str)` is exactly the `ActionEnvelope` pattern the
notebook validated. `ActionPicker.with_structured_output(Action)` already works correctly.
The pattern match bug (matching on `action` instead of `action.act`) is already fixed.
The `get_action_*` extractors are the only genuine redundancy left.

---

### Revised proposed approach (Option C — minimal, low risk)

1. **Keep `Action` and `Actions` as-is.** Correct shape for the LLM boundary.
2. **Remove the 4 specific `get_action_*` methods** — replaced by the already-added generic `get_action_typed`.
3. **Rewrite dispatch in `Player.play`** using `case ActionMove() as act:` with inline `wrsp = await` calls.
4. **Keep handler signatures as `action: Action`** — handlers call `action.get_action_typed(ActionMove)` internally. Uniform signatures, self-contained handlers.
5. **Add `async def ainvoke` to `ActionPicker`** using `self.chain.ainvoke`.
6. **Wire `Player.think()` to `ActionPicker.ainvoke`.**
7. `Brain` / full LLM wiring deferred.

If `reason` on the concrete type matters later, that is the right time to pursue Option A
(drop `reason` from the wrapper, move it into `BaseAction`), as it requires a deliberate schema
change and LLM prompt update.
