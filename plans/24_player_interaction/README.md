# Player-to-player interaction

Add `ActionInteract` to the action union. When a player picks it, the world delivers the target player's `to_prompt()` and routes a natural-language message between the two. This opens the door to cooperative mission-solving and emergent social behavior.

---

## Plan B - Peer-to-peer direct queue

The world acts only as a router and proximity guard. The target player runs its own LLM to produce the reply, keeping each agent's voice coherent with its own missions and history.

---

### Deadlock analysis (N players)

`WorldRunner.simulate()` is a single-task asyncio loop:

```
while True:
    req  = await world_input_queue.get()   # suspend until message
    wrsp = await handle_player_input(req)  # may suspend during LLM call
    await req.response_queue.put(wrsp)
```

**While the world is executing `handle_player_input`, it cannot process any other request.**

If `receive_message` (called from inside `handle_player_input`) itself puts a `WReq` onto `world_input_queue` and then awaits a response on its own `input_queue`, the dependency cycle becomes:

```
world  ──waiting for──▶  receive_message
receive_message  ──waiting for──▶  world  (blocked above)
```

With N players the graph grows. Player A interacts with B; if B's reply logic touches world services, it deadlocks. If B's reply logic is also allowed to interact with C, C with D, and so on, the potential for long-chain or even cyclic waits multiplies with player count.

**Root-cause invariant:** any coroutine called directly by the world loop (i.e. called inside `await handle_player_input`) must never put a message onto `world_input_queue` or await `input_queue.get()`. If that invariant is upheld for every player and every N, deadlock is impossible.

---

### Two strategies to uphold the invariant permanently

#### Strategy 1 - Structural isolation (recommended first step)

Make it architecturally impossible for `receive_message` to reach `world_input_queue`.

- Extract a pure `PlayerReplier` dataclass (mirrors `ActionPicker`) that only accepts frozen, plain-value inputs - no asyncio objects.
- `receive_message` is a pure coroutine on `Player` that only calls `PlayerReplier.ainvoke(...)` and reads `self` state; it never receives a reference to `world_input_queue`.
- The world calls it as `reply = await target.receive_message(snapshot)` where `snapshot` carries only serialisable data (sender name, sender prompt string, message text).
- Because `PlayerReplier` only awaits network I/O to an external LLM provider, the world loop is guaranteed to resume once the LLM responds.

**Proof for N players:** no matter how many players exist, each `receive_message` call is bounded by one external LLM round-trip and zero world I/O. The world loop unblocks after that single await, regardless of N.

**Enforcement:** code-review rule plus a lint check - `receive_message` must not import or accept `asyncio.Queue`. A `# noqa` comment on any queue usage in that method is a red flag.

#### Strategy 2 - Async inbox (scales to large N, enables broadcast)

The world never blocks at all during interaction handling.

1. Each `Player` gains `message_inbox: asyncio.Queue[InboxMessage]` and `reply_inbox: asyncio.Queue[WResInteract]`.
2. `handle_player_input(WRecInteract)`: look up target, do proximity check, put an `InboxMessage` onto `target.message_inbox` (non-blocking since the queue is never full in practice), immediately return `WResInteract(status=DELIVERED, reply=None)` to the sender.
3. The target player's `play()` loop drains `message_inbox` between each action cycle (a simple `while not self.message_inbox.empty()` guard). For each message it calls `await self.reply_to(msg)`, which runs the LLM and sends a `WRecInteractReply` to the world.
4. `handle_player_input(WRecInteractReply)`: look up the original sender by name, put `WResInteract(reply=...)` onto `sender.reply_inbox`.
5. The original sender picks up the reply on its next cycle from `reply_inbox` and logs it to `MissionHistory`.

**Proof for N players:** the world never suspends waiting for any player LLM. All interaction is fully non-blocking from the world's perspective. Chain interactions (A talks to B, B later talks to C) are naturally ordered through the inbox drain cycle with zero possibility of circular waits.

**Cost:** replies are asynchronous - A does not receive B's reply in the same action cycle. This is actually more realistic for a social simulation and naturally supports one-to-many (broadcast) messages.

---

### Chosen approach for this implementation: Strategy 1

Strategy 1 matches the existing architecture exactly (one synchronous exchange per action), keeps the `WReq`/`WRes` contract intact, and is trivially testable. Strategy 2 is the upgrade path if player counts grow large enough that sequential LLM calls in `receive_message` become a throughput bottleneck.

---

### New types

#### `src/laife/entities/action.py`

```python
class ActionInteract(BaseAction):
    """Address a natural-language message to a nearby player."""

    target_name: str = Field(..., description="Name of the player to address.")
    message: str = Field(..., description="The message to send.")
```

Update the union:

```python
Actions = ActionMove | ActionBuild | ActionCraft | ActionPlan | ActionInteract
```

`ActionPickerInput` gains no new fields - the existing `observation` already contains nearby player names once `WResObserve` surfaces them in `WorldMapObservation`.

#### `src/laife/entities/world_channel.py`

```python
class WRecInteract(WReq):
    """Request to route a message from one player to another."""

    sender_name: str
    sender_prompt: str   # snapshot of sender.to_prompt() at send time
    target_name: str
    message: str


class WResInteract(WRes):
    """Response carrying the target player's LLM-generated reply."""

    target_prompt: str   # snapshot of target.to_prompt() at reply time
    reply: str
```

#### `src/laife/llm/player_replier.py` (new file)

Mirrors `PlayerBrain` / `ActionPicker`. Uses a `StructuredLLMChain` with:

```python
class PlayerReplyInput(BaseModelKwargs):
    sender_name: str
    sender_prompt: str
    message: str
    own_state: str        # receiver's render_state()
    own_mission: str      # receiver's mission.to_prompt()
    own_history: str      # receiver's history.to_prompt()

class PlayerReplyOutput(BaseModel):
    reply: str
```

```python
@dataclass
class PlayerReplier:
    chat_config: ChatConfig
    prompt_str: str

    def __post_init__(self) -> None:
        self._chain: StructuredLLMChain[PlayerReplyInput, PlayerReplyOutput] = StructuredLLMChain(
            chat_config=self.chat_config,
            prompt_str=self.prompt_str,
            input_model=PlayerReplyInput,
            output_model=PlayerReplyOutput,
        )

    async def ainvoke(self, reply_input: PlayerReplyInput) -> PlayerReplyOutput:
        return await self._chain.ainvoke(reply_input)
```

---

### Changes to existing files

#### `src/laife/entities/player.py`

1. **`to_prompt() -> str`** - new public method (already used by README spec as the identity snapshot):

   ```python
   def to_prompt(self) -> str:
       return (
           f"Name: {self.name}\n"
           f"Type: {self.player_type}\n"
           f"Position: {self.position}\n"
           f"Mission: {self.mission.to_prompt()}"
       )
   ```

2. **`PlayerReplier` instantiation** in `__init__`, alongside `self.brain` and `self.planner`:

   ```python
   self.replier = PlayerReplier(
       PlayerReplierConfig(
           chat_config=laife_params.llm_services.chat.default,
           prompt_loader_config=PromptLoaderConfig(
               base_prompt_fol=laife_params.paths.prompts_fol,
               prompt_name="player_reply",
           ),
       )
   )
   ```

3. **`receive_message`** - pure coroutine, no queue refs, no world I/O:

   ```python
   async def receive_message(
       self,
       sender_name: str,
       sender_prompt: str,
       message: str,
   ) -> str:
       """Generate a reply to an incoming message using this player's own LLM context.

       This method must never put anything onto world_input_queue.
       It is called directly by WorldRunner inside handle_player_input.
       """
       result = await self.replier.ainvoke(
           PlayerReplyInput(
               sender_name=sender_name,
               sender_prompt=sender_prompt,
               message=message,
               own_state=self.render_state(),
               own_mission=self.mission.to_prompt(),
               own_history=self.history.to_prompt(),
           )
       )
       return result.reply
   ```

4. **`interact`** action handler:

   ```python
   async def interact(self, action: ActionInteract) -> WResInteract:
       alg.log(f"PLAYER.interact {self.name}: messaging {action.target_name!r}")
       wreq = WRecInteract(
           sender_name=self.name,
           sender_prompt=self.to_prompt(),
           target_name=action.target_name,
           message=action.message,
           response_queue=self.input_queue,
       )
       await self.world_input_queue.put(wreq)
       wrsp = cast("WResInteract", await self.input_queue.get())
       self.input_queue.task_done()
       alg.log(f"PLAYER.interact {self.name}: got reply {wrsp.reply!r}")
       return wrsp
   ```

5. **`play()` dispatch** - add the new case:

   ```python
   case ActionInteract() as act:
       wrsp = await self.interact(act)
   ```

   The resulting `MissionHistoryEntry` is logged identically to other actions.

#### `src/laife/entities/world_runner.py`

1. Import `WRecInteract`, `WResInteract`, `ActionInteract`.

2. Add `case WRecInteract():` in `handle_player_input`:

   ```python
   case WRecInteract():
       wrsp = await self.route_interaction(player_input)
   ```

3. New handler:

   ```python
   async def route_interaction(self, req: WRecInteract) -> WResInteract | WResError:
       """Proximity-check then route a message to the target player."""
       target = next((p for p in self.players if p.name == req.target_name), None)
       if target is None:
           return WResError(
               status=WResStatus.ERROR,
               message=f"No player named {req.target_name!r}.",
           )
       # Optional: enforce proximity using existing euclidean helper
       # (skip for first iteration, add as a config param later)
       reply = await target.receive_message(
           sender_name=req.sender_name,
           sender_prompt=req.sender_prompt,
           message=req.message,
       )
       return WResInteract(
           status=WResStatus.SUCCESS,
           target_prompt=target.to_prompt(),
           reply=reply,
       )
   ```

---

### New prompt

**`src/laife/prompts/player_reply/v1.jinja`**

Variables: `sender_name`, `sender_prompt`, `message`, `own_state`, `own_mission`, `own_history`.

The template should instruct the LLM to reply in character as the receiving player, informed by that player's current mission and recent history.

---

### New files summary

| Path                                        | Purpose                                                                                    |
| ------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `src/laife/llm/player_replier.py`           | `PlayerReplier` + `PlayerReplierConfig` + `PlayerReplyInput` / `PlayerReplyOutput`         |
| `src/laife/prompts/player_reply/v1.jinja`   | Jinja2 reply prompt                                                                        |
| `tests/entities/test_player_interaction.py` | Unit tests for `route_interaction`, `receive_message`, and full round-trip with mocked LLM |

---

### Test plan (`tests/entities/test_player_interaction.py`)

- `test_route_interaction_unknown_target` - world returns `WResError` when `target_name` not in `self.players`.
- `test_route_interaction_calls_receive_message` - mock `target.receive_message`; assert `route_interaction` calls it with correct `sender_name`, `sender_prompt`, `message`.
- `test_receive_message_never_touches_world_queue` - assert `world_input_queue` is empty after `receive_message` runs (structural invariant check).
- `test_full_round_trip` - two `Player` instances sharing a `WorldRunner` with `input_queue`; A sends interact action, assert B's `PlayerReplier` is invoked, A's `MissionHistory` receives the exchange.
- `test_n_player_no_deadlock` - spin up 4 players all posting `WRecInteract` to the world in quick succession with mocked LLM; assert all 4 eventually receive WResInteract with no timeout.

---

### Upgrade path to Strategy 2

When player count grows and sequential LLM calls in `receive_message` become a bottleneck:

1. Replace `await target.receive_message(...)` in `route_interaction` with `target.message_inbox.put_nowait(InboxMessage(...))` and return `WResInteract(status=DELIVERED, reply=None)` immediately.
2. Add `message_inbox` drain at the top of `Player.play()`.
3. Add `WRecInteractReply` / reply routing in `WorldRunner`.
4. The sender checks `reply_inbox` between actions or treats `DELIVERED` as sufficient for mission logging.

No changes to `ActionInteract`, `WRecInteract` shape, or the prompt are required - the upgrade is contained to `Player.__init__`, `Player.play()`, and `WorldRunner.route_interaction`.
