# Player inventory

Add an `inventory: list[Utensil]` to `Player`. Track utensils obtained via crafting (when a craft request succeeds, place the utensil in inventory). Let the brain see the inventory in its prompt so it can reason about what tools are available before deciding to craft or use one.

## Motivation

Currently, `Player.craft()` sends a `WRecCraft` to the world and discards the response aside from recording it in mission history. The crafted utensil is never stored anywhere, so the player has no memory of what it already owns. The brain also receives no inventory context, so it may repeatedly craft the same utensil or attempt actions that require a tool it already has.

## Steps

### 1. Add `inventory` to `Player`

In `src/laife/entities/player.py`, add an instance field to `__init__`:

```python
from laife.entities.utensil import Utensil

self.inventory: list[Utensil] = []
```

Add an `inventory_to_prompt()` helper that formats the list for the LLM:

```python
def inventory_to_prompt(self) -> str:
    if not self.inventory:
        return "Empty - no utensils carried."
    return "\n".join(f"- {u.to_prompt()}" for u in self.inventory)
```

### 2. Populate inventory after a successful craft

In `Player.craft()`, after receiving a `SUCCESS` response, construct a `Utensil` from the action fields and append it:

```python
async def craft(self, action: ActionCraft) -> WRes:
    ...
    wrsp = await self.input_queue.get()
    self.input_queue.task_done()
    if wrsp.status == WResStatus.SUCCESS:
        utensil = Utensil(name=action.utensil_name, description=action.description)
        self.inventory.append(utensil)
        alg.log(f"PLAYER.craft {self.name}: added {utensil.name} to inventory")
    alg.log(f"PLAYER.craft {self.name}: got response {wrsp}")
    return wrsp
```

The utensil fields are taken from the action (already validated by the world judge) rather than the response payload, keeping `WRes` unchanged for now.

### 3. Add `inventory` to `ActionPickerInput`

In `src/laife/entities/action.py`, add an `inventory` field to `ActionPickerInput`:

```python
class ActionPickerInput(BaseModelKwargs):
    mission: str
    history: str
    observation: str
    player_state: str
    inventory: str  # new
```

Because `StructuredLLMChain` validates that all input fields appear in the prompt template, this change will require a new prompt version (step 4).

### 4. Add `player_brain/v2.jinja`

Create `src/laife/prompts/player_brain/v2.jinja` by copying `v1.jinja` and inserting an inventory section before the action instructions:

```jinja
...
## Inventory
{{ inventory }}

Based on the above context...
```

`PromptLoader` with `version="auto"` will automatically pick `v2`. Never edit `v1.jinja`.

### 5. Pass `inventory` through to the brain

In `Player.think()`, forward `inventory_to_prompt()` to `self.brain.think()`:

```python
action = await self.brain.think(
    mission=self.mission,
    history=self.history,
    observation=self.last_observation,
    player_state=self.render_state(),
    inventory=self.inventory_to_prompt(),  # new
)
```

Propagate the parameter through `PlayerBrain.think()` and `ActionPicker.ainvoke()` - both delegate to `StructuredLLMChain` via `ActionPickerInput`, so the chain will automatically include the field.

### 6. Tests

Add `tests/entities/test_player_inventory.py`:

- `test_inventory_empty_on_init` - new player has `inventory == []`
- `test_craft_success_adds_utensil` - mock world returning `WResStatus.SUCCESS`; assert utensil is in `player.inventory` with correct name and description
- `test_craft_failure_does_not_add_utensil` - mock world returning `WResStatus.ERROR`; assert inventory remains empty
- `test_inventory_to_prompt_empty` - returns the "empty" string
- `test_inventory_to_prompt_with_items` - lists each utensil's `to_prompt()` on its own line

Add a test in `tests/llm/test_player_brain.py` (or new file) to confirm `ActionPickerInput` requires `inventory` and the `v2.jinja` template contains `{{ inventory }}`.

## Files changed

| File                                      | Change                                                                            |
| ----------------------------------------- | --------------------------------------------------------------------------------- |
| `src/laife/entities/player.py`            | Add `inventory`, `inventory_to_prompt()`, update `craft()`, update `think()` call |
| `src/laife/entities/action.py`            | Add `inventory: str` to `ActionPickerInput`                                       |
| `src/laife/prompts/player_brain/v2.jinja` | New prompt with `{{ inventory }}` section                                         |
| `tests/entities/test_player_inventory.py` | New test file                                                                     |

## Out of scope

- Typed `WRes` subclasses (tracked separately as plan item 2)
- Using the inventory in the world judge prompts (e.g., requiring ownership of a utensil to craft)
- Displaying inventory in the Pygame UI
- Removing utensils from inventory when used
