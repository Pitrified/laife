"""Tests for player-to-player interaction (ActionInteract / WRecInteract)."""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from laife.entities.action import ActionInteract
from laife.entities.player import Player
from laife.entities.world_channel import WRecInteract
from laife.entities.world_channel import WResError
from laife.entities.world_channel import WResInteract
from laife.entities.world_channel import WResStatus
from laife.entities.world_runner import WorldRunner

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_player(runner: WorldRunner, name: str = "alice") -> Player:
    """Create a Player with all LLM components mocked out."""
    with patch.multiple(
        "laife.entities.player",
        get_laife_params=MagicMock(return_value=MagicMock()),
        PlayerBrainConfig=MagicMock(),
        PlayerPlannerConfig=MagicMock(),
        PlayerReplierConfig=MagicMock(),
        PromptLoaderConfig=MagicMock(),
        PlayerBrain=MagicMock(return_value=MagicMock()),
        PlayerPlanner=MagicMock(return_value=MagicMock()),
        PlayerReplier=MagicMock(return_value=MagicMock()),
    ):
        player = Player(
            name=name,
            position=(0, 0),
            player_type="hero",
            world_input_queue=runner.input_queue,
        )
    runner.add_player(player)
    return player


# ---------------------------------------------------------------------------
# ActionInteract shape
# ---------------------------------------------------------------------------


def test_action_interact_fields() -> None:
    """ActionInteract must carry target_name, message, and reason."""
    action = ActionInteract(
        reason="Ask for help.",
        target_name="bob",
        message="Can you pass me a sword?",
    )
    assert action.target_name == "bob"
    assert action.message == "Can you pass me a sword?"
    assert action.reason == "Ask for help."


# ---------------------------------------------------------------------------
# WRecInteract / WResInteract shape
# ---------------------------------------------------------------------------


def test_wrecinteract_str() -> None:
    """WRecInteract.__str__ must include sender, target, and message."""
    q: asyncio.Queue = asyncio.Queue()
    req = WRecInteract(
        sender_name="alice",
        sender_prompt="Name: alice",
        target_name="bob",
        message="Hello!",
        response_queue=q,
    )
    s = str(req)
    assert "alice" in s
    assert "bob" in s
    assert "Hello!" in s


def test_wresinteract_str() -> None:
    """WResInteract.__str__ must include the reply."""
    res = WResInteract(status=WResStatus.SUCCESS, target_prompt="Name: bob", reply="Hi there!")
    assert "Hi there!" in str(res)


# ---------------------------------------------------------------------------
# Player.to_prompt
# ---------------------------------------------------------------------------


def test_player_to_prompt_contains_name_position() -> None:
    """to_prompt must include the player's name and position."""
    runner = WorldRunner()
    player = _make_player(runner, name="charlie")
    prompt = player.to_prompt()
    assert "charlie" in prompt
    assert "0" in prompt  # position (0, 0)


# ---------------------------------------------------------------------------
# WorldRunner.route_interaction - unknown target
# ---------------------------------------------------------------------------


def test_route_interaction_unknown_target() -> None:
    """route_interaction must return WResError when target is not registered."""
    q: asyncio.Queue = asyncio.Queue()
    runner = WorldRunner()
    _make_player(runner, name="alice")

    req = WRecInteract(
        sender_name="alice",
        sender_prompt="Name: alice",
        target_name="ghost",
        message="You there?",
        response_queue=q,
    )
    result = asyncio.run(runner.route_interaction(req))

    assert isinstance(result, WResError)
    assert result.status == WResStatus.ERROR
    assert "ghost" in result.message


# ---------------------------------------------------------------------------
# WorldRunner.route_interaction - delegates to receive_message
# ---------------------------------------------------------------------------


def test_route_interaction_calls_receive_message() -> None:
    """route_interaction must call target.receive_message with correct args."""
    q: asyncio.Queue = asyncio.Queue()
    runner = WorldRunner()
    _make_player(runner, name="alice")
    bob = _make_player(runner, name="bob")

    bob.receive_message = AsyncMock(return_value="Sure, one sec.")

    req = WRecInteract(
        sender_name="alice",
        sender_prompt="Name: alice",
        target_name="bob",
        message="Can you help me?",
        response_queue=q,
    )
    result = asyncio.run(runner.route_interaction(req))

    bob.receive_message.assert_awaited_once_with(
        sender_name="alice",
        sender_prompt="Name: alice",
        message="Can you help me?",
    )
    assert isinstance(result, WResInteract)
    assert result.reply == "Sure, one sec."
    assert result.status == WResStatus.SUCCESS


# ---------------------------------------------------------------------------
# Player.receive_message - never touches world_input_queue (deadlock invariant)
# ---------------------------------------------------------------------------


def test_receive_message_never_touches_world_queue() -> None:
    """receive_message must not put anything onto world_input_queue.

    This is the central deadlock-safety invariant for Strategy 1.
    """
    runner = WorldRunner()
    player = _make_player(runner, name="alice")

    player.replier.ainvoke = AsyncMock(return_value=MagicMock(reply="I'm fine, thanks."))

    queue_size_before = runner.input_queue.qsize()
    reply = asyncio.run(
        player.receive_message(
            sender_name="bob",
            sender_prompt="Name: bob",
            message="How are you?",
        )
    )
    queue_size_after = runner.input_queue.qsize()

    assert reply == "I'm fine, thanks."
    assert queue_size_after == queue_size_before, (
        "receive_message must not put anything onto world_input_queue"
    )


# ---------------------------------------------------------------------------
# Full round-trip: player A sends, player B replies
# ---------------------------------------------------------------------------


def test_full_round_trip() -> None:
    """Player A sends ActionInteract; B's replier is invoked; A gets WResInteract."""

    async def _run() -> WResInteract | WResError:
        runner = WorldRunner()
        alice = _make_player(runner, name="alice")
        bob = _make_player(runner, name="bob")

        bob.replier.ainvoke = AsyncMock(return_value=MagicMock(reply="Happy to help!"))

        action = ActionInteract(
            reason="Need assistance.",
            target_name="bob",
            message="Can you help me build a house?",
        )

        sim_task = asyncio.create_task(runner.simulate())
        result = await alice.interact(action)
        sim_task.cancel()
        return result

    result = asyncio.run(_run())

    assert isinstance(result, WResInteract)
    assert result.status == WResStatus.SUCCESS
    assert result.reply == "Happy to help!"


# ---------------------------------------------------------------------------
# N-player no-deadlock stress test
# ---------------------------------------------------------------------------


def test_n_player_no_deadlock() -> None:
    """Four players all send WRecInteract to the world without deadlocking.

    Each player targets the next one in a ring (A->B->C->D->A).
    All four must receive WResInteract within the timeout.
    """

    async def _run() -> list[WResInteract | WResError]:
        runner = WorldRunner()
        names = ["alpha", "beta", "gamma", "delta"]
        players = [_make_player(runner, name=n) for n in names]

        for p in players:
            p.replier.ainvoke = AsyncMock(return_value=MagicMock(reply=f"Reply from {p.name}"))

        async def send_interact(sender: Player, target_name: str) -> WResInteract | WResError:
            action = ActionInteract(
                reason="stress test",
                target_name=target_name,
                message=f"Hello from {sender.name}",
            )
            return await sender.interact(action)

        sim_task = asyncio.create_task(runner.simulate())
        results = await asyncio.wait_for(
            asyncio.gather(
                send_interact(players[0], names[1]),
                send_interact(players[1], names[2]),
                send_interact(players[2], names[3]),
                send_interact(players[3], names[0]),
            ),
            timeout=10.0,
        )
        sim_task.cancel()
        return list(results)

    results = asyncio.run(_run())

    for res in results:
        assert isinstance(res, WResInteract), f"Expected WResInteract, got {type(res)}: {res}"
        assert res.status == WResStatus.SUCCESS
