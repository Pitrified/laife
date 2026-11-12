# Move delta loop

Player moves with main `ActionMove`.

Internally we

1. save the starting position
2. move in delta steps, each one validated by the world with deterministic collision system
3. if collided, return the collision feedback to the player, and let it think again
4. if not collided, update the position and continue until the total delta is reached

---

## Detailed plan

### Overview

`ActionMove` already carries `direction: CardinalDirection` and `distance: int` (the LLM's intent).
The execution model turns that single LLM action into `distance` one-step world requests.
The world owns the authoritative position and the collision check; the player only proposes.

---

### Step 1 - `directions.py`: add `cardinal_to_delta()`

**File:** `src/laife/entities/utils/directions.py`

Add a pure function that maps each `CardinalDirection` to a `(dx, dy)` unit vector.
Pygame's y-axis points downward, so North is `(0, -1)`, South is `(0, +1)`, etc.

```python
def cardinal_to_delta(direction: CardinalDirection, step: int = 1) -> tuple[int, int]:
    """Return the (dx, dy) step vector for a cardinal direction.

    Coordinate convention: x increases East, y increases South (pygame).
    `step` scales the unit vector, enabling non-unit steps.
    """
    _UNIT: dict[CardinalDirection, tuple[int, int]] = {
        CardinalDirection.North:     ( 0, -1),
        CardinalDirection.South:     ( 0, +1),
        CardinalDirection.East:      (+1,  0),
        CardinalDirection.West:      (-1,  0),
        CardinalDirection.NorthEast: (+1, -1),
        CardinalDirection.NorthWest: (-1, -1),
        CardinalDirection.SouthEast: (+1, +1),
        CardinalDirection.SouthWest: (-1, +1),
    }
    ux, uy = _UNIT[direction]
    return ux * step, uy * step
```

---

### Step 2 - `world_channel.py`: add `WRecMove`

**File:** `src/laife/entities/world_channel.py`

Add a world-channel message the player sends **once per delta step**.
It carries the proposed next position; the world returns success or an error with feedback.

```python
class WRecMove(WReq):
    """Request to move a player to a new position (one delta step)."""

    def __init__(
        self,
        player: "Player",
        new_position: Position,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.player = player
        self.new_position = new_position
```

The `WRes.response_data` on collision will include `"obstacle"` (the blocking entity's string
representation) so the LLM gets meaningful feedback.

---

### Step 3 - `world_runner.py`: implement `move_player()`

**File:** `src/laife/entities/world_runner.py`

1. Add `case WRecMove()` in `handle_player_input`.
2. Implement `move_player(req: WRecMove) -> WRes`:
   - Read the player's footprint from `req.player.size` (set in `Player.__init__`, default `(1, 1)`).
   - Check `aabb_collides` of the proposed position against every building and every other player.
   - On no collision: return `SUCCESS` - **do not mutate the player's position here**; the player
     updates its own position after receiving the success response.
   - On collision: return `ERROR` with `{"obstacle": str(blocker), "at": req.new_position}`.

---

### Step 4 - `player.py`: rewrite `Player.move()`

**File:** `src/laife/entities/player.py`

Replace the `asyncio.sleep` stub with the delta loop:

```python
async def move(self, action: ActionMove) -> WRes:
    self.state = PlayerState.MOVING
    start_position = self.position          # snapshot for logging / rollback
    dx, dy = cardinal_to_delta(action.direction)

    for step in range(action.distance):
        new_pos = (self.position[0] + dx, self.position[1] + dy)
        wreq = WRecMove(player=self, new_position=new_pos,
                        response_queue=self.input_queue)
        await self.world_input_queue.put(wreq)
        wrsp = await self.input_queue.get()
        self.input_queue.task_done()

        if wrsp.status == WResStatus.ERROR:
            # Collision - report back to the brain so it can re-plan
            self.state = PlayerState.IDLE
            return WRes(
                WResStatus.ERROR,
                {
                    "message": (
                        f"Blocked after {step} step(s) from {start_position}. "
                        f"Obstacle: {wrsp.response_data.get('obstacle', 'unknown')}."
                    ),
                },
            )

        # World validated the step - player owns its position update
        self.position = new_pos

    self.state = PlayerState.IDLE
    return WRes(WResStatus.SUCCESS, {"message": f"Moved {action.distance} step(s)."})
```

The world never mutates `player.position`; it only validates the proposed position and
returns `SUCCESS` or `ERROR`. The player advances `self.position = new_pos` on each
successful step, keeping it as the authoritative owner of its own state.

---

### Step 5 - tests

**File:** `tests/entities/test_move_delta.py`

Key test cases (all run with a real `WorldRunner` + `asyncio.run` / `pytest-asyncio`):

| Test                                    | Setup                                      | Expected                                                         |
| --------------------------------------- | ------------------------------------------ | ---------------------------------------------------------------- |
| `test_move_free_path`                   | Player at (0,0), no buildings, move East 3 | `SUCCESS`, position (3,0)                                        |
| `test_move_blocked_immediately`         | Building at (1,0), move East 3             | `ERROR` after 0 steps, position (0,0)                            |
| `test_move_blocked_mid_path`            | Building at (2,0), move East 3             | `ERROR` after 1 step, position (1,0)                             |
| `test_move_feedback_message`            | Any collision                              | `response_data["message"]` contains `"Blocked"` and `"Obstacle"` |
| `test_cardinal_to_delta_all_directions` | Pure unit test                             | Each direction maps to the correct `(dx, dy)`                    |

---

### File change summary

| File                                     | Change                                                            |
| ---------------------------------------- | ----------------------------------------------------------------- |
| `src/laife/entities/utils/directions.py` | Add `cardinal_to_delta(direction, step=1)`                        |
| `src/laife/entities/world_channel.py`    | Add `WRecMove`                                                    |
| `src/laife/entities/world_runner.py`     | Add `case WRecMove` + implement `move_player()` (read-only world) |
| `src/laife/entities/player.py`           | Add `size: Size = (1,1)` to `__init__`; rewrite `move()` loop     |
| `tests/entities/test_move_delta.py`      | New test file (5 cases above)                                     |

No changes to `ActionMove`, `aabb_collides`, or any prompt/LLM layer.
