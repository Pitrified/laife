# Upgrade: Strategy 1 -> Strategy 2 (async-inbox interactions)

**When to apply:** when sequential LLM calls inside `route_interaction` become a
throughput bottleneck - i.e. the world loop pauses for one full LLM round-trip per
interaction, and that latency is unacceptable with N players sending many messages
per second.

**What changes:** the world becomes purely non-blocking for interactions; replies
arrive asynchronously in the sender's next action cycle.

**What does NOT change:** `ActionInteract`, `WRecInteract`, the `player_reply`
prompt, and `PlayerReplier` are all untouched.

---

## New types

### `src/laife/entities/world_channel.py`

Add alongside the existing `WRecInteract` / `WResInteract`:

```python
class InboxMessage(BaseModel):
    """A message dropped into a player's inbox by the world router."""

    sender_name: str
    sender_prompt: str
    message: str


class WRecInteractReply(WReq):
    """A player posts this after generating its async reply."""

    def __init__(
        self,
        original_sender_name: str,
        reply: str,
        replier_prompt: str,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.original_sender_name = original_sender_name
        self.reply = reply
        self.replier_prompt = replier_prompt
```

`WResInteract` already carries `reply: str` and `target_prompt: str` - no changes
needed there, but callers must tolerate `reply` being an empty string when
`status == DELIVERED` (new status value below).

### Update `WResStatus`

```python
class WResStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    DELIVERED = "delivered"   # NEW - message enqueued; reply is async
```

---

## Changes to `src/laife/entities/player.py`

### 1. Add `message_inbox` and `reply_inbox` in `__init__`

```python
self.message_inbox: asyncio.Queue[InboxMessage] = asyncio.Queue()
self.reply_inbox: asyncio.Queue[WResInteract] = asyncio.Queue()
```

### 2. Replace `interact` (sender side)

The sender no longer awaits a reply in the same cycle. It sends `WRecInteract` and
receives `WResInteract(status=DELIVERED, reply="")` immediately.

```python
async def interact(self, action: ActionInteract) -> WResInteract | WResError:
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
    alg.log(f"PLAYER.interact {self.name}: message delivered, reply pending")
    return wrsp
```

### 3. Add `reply_to` (receiver side - generates and posts reply)

```python
async def reply_to(self, msg: InboxMessage) -> None:
    """Generate an in-character reply and post it back via the world router."""
    reply_text = await self.receive_message(
        sender_name=msg.sender_name,
        sender_prompt=msg.sender_prompt,
        message=msg.message,
    )
    wreq = WRecInteractReply(
        original_sender_name=msg.sender_name,
        reply=reply_text,
        replier_prompt=self.to_prompt(),
        response_queue=self.input_queue,
    )
    await self.world_input_queue.put(wreq)
    # Drain the ACK (a bare WRes(status=SUCCESS)) so the queue stays clean
    _ = await self.input_queue.get()
    self.input_queue.task_done()
```

### 4. Drain `message_inbox` at the top of `play()`

```python
async def play(self) -> None:
    while True:
        # Drain any incoming messages before deciding the next action
        while not self.message_inbox.empty():
            msg = self.message_inbox.get_nowait()
            self.message_inbox.task_done()
            await self.reply_to(msg)

        # Drain any replies that arrived for messages we sent earlier
        while not self.reply_inbox.empty():
            incoming = self.reply_inbox.get_nowait()
            self.reply_inbox.task_done()
            he = MissionHistoryEntry(
                action=ActionInteract(
                    reason="received async reply",
                    target_name=incoming.target_prompt[:20],
                    message=incoming.reply,
                ),
                result=str(incoming),
            )
            self.history.add_history_entry(he)

        alg.log(f"PLAYER.play {self.name}: needs to {self.mission}")
        await self.observe()
        action = await self.think()
        match action:
            ... # unchanged
```

---

## Changes to `src/laife/entities/world_runner.py`

### 1. Replace `route_interaction` - now non-blocking

```python
async def route_interaction(self, req: WRecInteract) -> WResInteract | WResError:
    """Drop the message into the target's inbox and return DELIVERED immediately."""
    target = next((p for p in self.players if p.name == req.target_name), None)
    if target is None:
        return WResError(
            status=WResStatus.ERROR,
            message=f"No player named {req.target_name!r} exists in the world.",
        )
    target.message_inbox.put_nowait(
        InboxMessage(
            sender_name=req.sender_name,
            sender_prompt=req.sender_prompt,
            message=req.message,
        )
    )
    return WResInteract(
        status=WResStatus.DELIVERED,
        target_prompt=target.to_prompt(),
        reply="",
    )
```

### 2. Add `handle_interact_reply` case in `handle_player_input`

```python
case WRecInteractReply():
    wrsp = await self.deliver_reply(player_input)
```

```python
async def deliver_reply(self, req: WRecInteractReply) -> WRes:
    """Forward an async reply to the original sender's reply_inbox."""
    sender = next((p for p in self.players if p.name == req.original_sender_name), None)
    if sender is None:
        return WResError(
            status=WResStatus.ERROR,
            message=f"Original sender {req.original_sender_name!r} no longer exists.",
        )
    await sender.reply_inbox.put(
        WResInteract(
            status=WResStatus.SUCCESS,
            target_prompt=req.replier_prompt,
            reply=req.reply,
        )
    )
    return WRes(status=WResStatus.SUCCESS)
```

---

## Test changes

- Update `test_full_round_trip`: sender now receives `DELIVERED`, bob's reply
  arrives in `alice.reply_inbox` after bob's next `play()` drain cycle.
- Update `test_n_player_no_deadlock`: no `asyncio.wait_for` needed since the world
  never blocks; assert `reply_inbox` is populated after running two `play()` drain
  cycles for each player.
- Remove `test_receive_message_never_touches_world_queue` (it no longer calls
  `receive_message` from inside the world loop; `reply_to` does, but via the normal
  `world_input_queue` path which is correct in Strategy 2).
- Add `test_route_interaction_is_nonblocking`: assert that `route_interaction`
  returns in under 1 ms (no LLM call inside).

---

## Containment summary

| File | Change type |
|---|---|
| `world_channel.py` | Add `InboxMessage`, `WRecInteractReply`; extend `WResStatus` |
| `player.py` | Add `message_inbox`, `reply_inbox`; replace `interact`; add `reply_to`; update `play()` |
| `world_runner.py` | Replace `route_interaction`; add `deliver_reply` + dispatch case |
| `test_player_interaction.py` | Update 3 tests, add 1 new test |

`ActionInteract`, `WRecInteract`, `PlayerReplier`, `PlayerReplyInput`,
and `src/laife/prompts/player_reply/v1.jinja` are **unchanged**.
