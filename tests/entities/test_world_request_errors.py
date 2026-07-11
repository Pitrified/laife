"""Tests for surviving WResError world responses (feature 35, phase 1)."""

import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from laife.entities.action import ActionBuild
from laife.entities.action import ActionInteract
from laife.entities.player import Player
from laife.entities.world_channel import WRecObserve
from laife.entities.world_channel import WResError
from laife.entities.world_channel import WResObserve
from laife.entities.world_channel import WResPlan
from laife.entities.world_channel import WResStatus
from laife.entities.world_map_observation import WorldMapObservation
from laife.entities.world_runner import WorldRunner
from laife.llm.mission import MissionStatus

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
        MissionGeneratorConfig=MagicMock(),
        MissionGenerator=MagicMock(return_value=MagicMock()),
    ):
        player = Player(
            name=name,
            position=(0, 0),
            player_type="hero",
            world_input_queue=runner.input_queue,
        )
    runner.add_player(player)
    return player


@pytest.fixture(autouse=True)
def _silence_alog() -> Generator[None]:
    """Prevent alg.log / slog from writing outside an event loop during tests."""
    with patch("laife.entities.player.alg"), patch("laife.entities.player.slog"):
        yield


# ---------------------------------------------------------------------------
# The captured incident: interact with a building name must not kill the game
# ---------------------------------------------------------------------------


def test_interact_with_unknown_target_returns_error() -> None:
    """interact() returns the routed WResError instead of raising TypeError."""

    async def _run() -> WResError | object:
        runner = WorldRunner()
        alice = _make_player(runner)
        action = ActionInteract(
            reason="To gather crops I need to interact with the farm.",
            target_name="Big ol Farm",
            message="I would like to gather crops.",
        )
        sim_task = asyncio.create_task(runner.simulate())
        result = await alice.interact(action)
        sim_task.cancel()
        return result

    result = asyncio.run(_run())

    assert isinstance(result, WResError)
    assert result.status == WResStatus.ERROR
    assert "Big ol Farm" in result.message


def test_play_survives_interact_error_and_continues() -> None:
    """A WResError turn lands in history and the play loop keeps going."""

    async def _run() -> Player:
        runner = WorldRunner()
        alice = _make_player(runner)
        alice.mission.status = MissionStatus.ACTIVE
        alice.brain.think = AsyncMock(
            return_value=ActionInteract(
                reason="Gather crops.",
                target_name="Big ol Farm",
                message="I would like to gather crops.",
            )
        )
        sim_task = asyncio.create_task(runner.simulate())
        play_task = asyncio.create_task(alice.play())
        # Let the loop run until at least two turns completed an error round trip.
        for _ in range(200):
            await asyncio.sleep(0)
            if alice.turn >= 2 and len(alice.history.history) >= 1:
                break
        play_task.cancel()
        sim_task.cancel()
        return alice

    alice = asyncio.run(_run())

    assert alice.turn >= 2, "the loop must survive the error and start another turn"
    assert alice.history.history, "the error must be recorded in history"
    assert "No player named" in alice.history.history[0].result
    assert alice.mission.status == MissionStatus.ACTIVE


# ---------------------------------------------------------------------------
# The fail-loudly contract stays for genuinely wrong types
# ---------------------------------------------------------------------------


def test_world_request_wrong_type_still_raises() -> None:
    """A response that is neither the expected type nor WResError raises."""

    async def _run() -> None:
        runner = WorldRunner()
        alice = _make_player(runner)
        alice.input_queue.put_nowait(
            WResPlan(status=WResStatus.SUCCESS, sub_missions=[], reason="")
        )
        wreq = WRecObserve(position=(0, 0), response_queue=alice.input_queue)
        await alice._world_request(wreq, WResObserve)

    with pytest.raises(TypeError, match="Expected WResObserve, got WResPlan"):
        asyncio.run(_run())


# ---------------------------------------------------------------------------
# Error responses stay mission-neutral and observation-safe
# ---------------------------------------------------------------------------


def test_update_mission_ignores_error_response() -> None:
    """A WResError to a build action must not drive a mission transition."""
    runner = WorldRunner()
    alice = _make_player(runner)
    alice.mission.status = MissionStatus.ACTIVE

    action = ActionBuild(reason="r", building_type="hut", description="d", size=1)
    wrsp = WResError(status=WResStatus.ERROR, message="boom")
    alice._update_mission_from_response(action, wrsp)

    assert alice.mission.status == MissionStatus.ACTIVE


def test_observe_error_keeps_stale_observation() -> None:
    """observe() returns the error and keeps the previously cached observation."""

    async def _run() -> tuple[Player, WResObserve | WResError]:
        runner = WorldRunner()
        alice = _make_player(runner)
        stale = alice.last_observation
        alice.input_queue.put_nowait(WResError(status=WResStatus.ERROR, message="no world"))
        result = await alice.observe()
        assert alice.last_observation is stale
        return alice, result

    _, result = asyncio.run(_run())

    assert isinstance(result, WResError)


def test_observe_success_updates_observation() -> None:
    """observe() still caches a fresh observation on the happy path."""

    async def _run() -> Player:
        runner = WorldRunner()
        alice = _make_player(runner)
        fresh = WorldMapObservation.from_position((3, 4))
        alice.input_queue.put_nowait(
            WResObserve(status=WResStatus.SUCCESS, observation=fresh)
        )
        await alice.observe()
        assert alice.last_observation is fresh
        return alice

    asyncio.run(_run())
