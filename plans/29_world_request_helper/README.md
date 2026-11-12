# Refactor repetitive player request pattern

Extract the "build request, send to world, await response, handle status,
record history" boilerplate in `Player` into a typed generic helper
`async _world_request[T: WRes](wreq, response_type) -> T`. Cuts duplication across the
move/build/craft/interact/observe handlers and makes adding new action types
cheaper.

---

## The repeated pattern

Every handler that talks to `WorldRunner` contains the same three lines:

```python
await self.world_input_queue.put(wreq)
wrsp = cast("WResXxx", await self.input_queue.get())
self.input_queue.task_done()
```

This is already present in five places (`observe`, `move` step loop, `build`,
`craft`, `interact`) and will appear in every new action type added. The cast is
also unsafe - if `WorldRunner` ever sends the wrong response type, the error
surfaces far from the dispatch site.

---

## Plan

### No new files

All changes are internal to `src/laife/entities/player.py`.

### Modified files

#### `src/laife/entities/player.py`

**Add `_world_request` helper**

Use Python 3.13 type-parameter syntax so the return type is narrowed to the
concrete `WRes` subclass at each call site. The helper performs an explicit
`isinstance` check and raises `TypeError` on mismatch. This catches world
implementation bugs at the boundary rather than letting them surface as
`AttributeError` deep in caller code.

```python
async def _world_request[T: WRes](self, wreq: WReq, response_type: type[T]) -> T:
    """Send *wreq* to the world, assert the response type, and return it.

    Raises TypeError if the world returns an unexpected response type.
    The world channel is expected to be reliable; a type mismatch signals
    a world implementation bug and should fail loudly.
    """
    await self.world_input_queue.put(wreq)
    wrsp = await self.input_queue.get()
    self.input_queue.task_done()
    if not isinstance(wrsp, response_type):
        msg = f"Expected {response_type.__name__}, got {type(wrsp).__name__}"
        raise TypeError(msg)
    return wrsp
```

The `cast(...)` calls are removed. Pyright infers the concrete return type from
`response_type`, so no further narrowing is needed at any call site.

**Refactor each handler**

| Handler           | Before                            | After                                                                   |
| ----------------- | --------------------------------- | ----------------------------------------------------------------------- |
| `observe`         | 3-line pattern + cast             | `wrsp = await self._world_request(wreq, WResObserve)`                   |
| `move` (per step) | 3-line pattern + cast inside loop | `wrsp_step = await self._world_request(wreq, WResMoveStep)` inside loop |
| `build`           | 3-line pattern + cast             | `wrsp = await self._world_request(wreq, WResBuild)`                     |
| `craft`           | 3-line pattern + cast             | `wrsp = await self._world_request(wreq, WResCraft)`                     |
| `interact`        | 3-line pattern + cast             | `wrsp = await self._world_request(wreq, WResInteract)`                  |

Pyright resolves the return type of each call to the concrete subclass, so
field access on the result (e.g. `wrsp.observation`, `wrsp.status`) is fully
type-checked without any additional `isinstance` guards or `cast` calls.

#### `tests/entities/test_player_lifecycle.py`

- Existing tests use `AsyncMock` for `world_input_queue.put` and
  `input_queue.get`. These still work unchanged because `_world_request` calls
  the same queue methods.
- Add `test_world_request_queues_and_returns`: verifies that `_world_request`
  puts to `world_input_queue` exactly once, calls `input_queue.get` exactly
  once, calls `input_queue.task_done` exactly once, and returns the response
  when its type matches `response_type`.
- Add `test_world_request_raises_on_wrong_type`: `input_queue.get` returns a
  `WResError` but `response_type=WResObserve`; asserts `TypeError` is raised.

### Sequence of changes

1. Add `_world_request` to `Player` with the docstring above.
2. Refactor `observe` - simplest case, one use.
3. Refactor `build` and `craft` - parallel, both single-round-trip.
4. Refactor `interact` - single-round-trip.
5. Refactor `move` step loop - extra care: `task_done` was inside the loop, the
   helper preserves that.
6. Update `tests/entities/test_player_lifecycle.py` with the new unit test.
7. Verify: `uv run pytest && uv run ruff check . && uv run pyright`.
