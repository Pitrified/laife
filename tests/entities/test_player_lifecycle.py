"""Tests for Player mission lifecycle - completion and failure transitions."""

import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from laife.entities.action import ActionBuild
from laife.entities.action import ActionCraft
from laife.entities.action import ActionMove
from laife.entities.action import ActionPlan
from laife.entities.player import Player
from laife.entities.utils.directions import CardinalDirection
from laife.entities.world_channel import WRecObserve
from laife.entities.world_channel import WResBuild
from laife.entities.world_channel import WResCraft
from laife.entities.world_channel import WResError
from laife.entities.world_channel import WResMove
from laife.entities.world_channel import WResObserve
from laife.entities.world_channel import WResStatus
from laife.entities.world_map_observation import WorldMapObservation
from laife.entities.world_runner import WorldRunner
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionHistoryEntry
from laife.llm.mission import MissionStatus
from laife.meta.log_events import EVT_WORLD_RESPONSE

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_player(runner: WorldRunner) -> Player:
    """Create a Player with all LLM components mocked out."""
    with patch.multiple(
        "laife.entities.player",
        get_laife_params=MagicMock(return_value=MagicMock()),
        PlayerBrainConfig=MagicMock(),
        PlayerPlannerConfig=MagicMock(),
        PlayerReplierConfig=MagicMock(),
        MissionGeneratorConfig=MagicMock(),
        PromptLoaderConfig=MagicMock(),
        PlayerBrain=MagicMock(return_value=MagicMock()),
        PlayerPlanner=MagicMock(return_value=MagicMock()),
        PlayerReplier=MagicMock(return_value=MagicMock()),
        MissionGenerator=MagicMock(return_value=MagicMock()),
    ):
        player = Player(
            name="tester",
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


@pytest.fixture
def player() -> Player:
    """Return a Player with an ACTIVE mission, connected to a fresh WorldRunner."""
    runner = WorldRunner()
    p = _make_player(runner)
    # Start in ACTIVE state so tests reason about transitions from a running mission.
    p.mission.status = MissionStatus.ACTIVE
    return p


# ---------------------------------------------------------------------------
# _update_mission_from_response
# ---------------------------------------------------------------------------


def test_build_success_completes_mission(player: Player) -> None:
    """A successful build response marks the mission COMPLETED."""
    action = ActionBuild(reason="need shelter", building_type="hut", description="a hut", size=1)
    wrsp = WResBuild(status=WResStatus.SUCCESS, feedback="Built!")
    player._update_mission_from_response(action, wrsp)
    assert player.mission.status == MissionStatus.COMPLETED


def test_build_error_increments_failure(player: Player) -> None:
    """A failed build response increments consecutive_failures without failing the mission."""
    action = ActionBuild(reason="need shelter", building_type="hut", description="a hut", size=1)
    wrsp = WResBuild(status=WResStatus.ERROR, feedback="No space.")
    player._update_mission_from_response(action, wrsp)
    assert player.mission.consecutive_failures == 1
    assert player.mission.status == MissionStatus.ACTIVE


def test_craft_success_completes_mission(player: Player) -> None:
    """A successful craft response marks the mission COMPLETED."""
    action = ActionCraft(reason="need tool", utensil_name="axe", description="a sharp axe")
    wrsp = WResCraft(status=WResStatus.SUCCESS, feedback="Crafted!")
    player._update_mission_from_response(action, wrsp)
    assert player.mission.status == MissionStatus.COMPLETED


def test_craft_error_increments_failure(player: Player) -> None:
    """A failed craft response increments consecutive_failures."""
    action = ActionCraft(reason="need tool", utensil_name="axe", description="a sharp axe")
    wrsp = WResCraft(status=WResStatus.ERROR, feedback="Missing materials.")
    player._update_mission_from_response(action, wrsp)
    assert player.mission.consecutive_failures == 1


def test_move_error_does_not_affect_mission(player: Player) -> None:
    """A move error response leaves the mission status and failure counter unchanged."""
    action = ActionMove(reason="exploring", direction=CardinalDirection.North, distance=1)
    wrsp = WResMove(status=WResStatus.ERROR, message="Blocked.")
    player._update_mission_from_response(action, wrsp)
    assert player.mission.status == MissionStatus.ACTIVE
    assert player.mission.consecutive_failures == 0


def test_n_build_errors_fail_mission(player: Player) -> None:
    """max_failures consecutive build errors mark the mission FAILED."""
    action = ActionBuild(reason="need shelter", building_type="hut", description="a hut", size=1)
    for _ in range(player.mission.max_failures):
        player._update_mission_from_response(
            action, WResBuild(status=WResStatus.ERROR, feedback="No space.")
        )
    assert player.mission.status == MissionStatus.FAILED


# ---------------------------------------------------------------------------
# _start_new_mission
# ---------------------------------------------------------------------------


def test_start_new_mission_resets_to_active(player: Player) -> None:
    """After a terminal mission, _start_new_mission creates a fresh ACTIVE mission."""
    player.mission.status = MissionStatus.COMPLETED
    player._start_new_mission("Craft a better axe")
    assert player.mission.status == MissionStatus.ACTIVE
    assert player.mission.objective == "Craft a better axe"


def test_start_new_mission_resets_consecutive_failures(player: Player) -> None:
    """The new mission starts with consecutive_failures at zero."""
    player.mission.consecutive_failures = 5
    player.mission.status = MissionStatus.FAILED
    player._start_new_mission("Build a watchtower")
    assert player.mission.consecutive_failures == 0


def test_start_new_mission_resets_history(player: Player) -> None:
    """_start_new_mission clears the mission history."""
    player.history.add_history_entry(
        MissionHistoryEntry(
            action=ActionPlan(reason="test"),
            result="ok",
        )
    )
    assert len(player.history.history) == 1
    player.mission.status = MissionStatus.COMPLETED
    player._start_new_mission("Find water")
    assert isinstance(player.history, MissionHistory)
    assert len(player.history.history) == 0


# ---------------------------------------------------------------------------
# _world_request
# ---------------------------------------------------------------------------


def test_world_request_queues_and_returns(player: Player) -> None:
    """_world_request must put once, get once, call task_done once, and return wrsp."""

    async def _run() -> WResObserve:
        obs = WResObserve(
            status=WResStatus.SUCCESS,
            observation=WorldMapObservation.from_position((0, 0)),
        )
        player.world_input_queue.put = AsyncMock()
        player.input_queue.get = AsyncMock(return_value=obs)
        player.input_queue.task_done = MagicMock()

        wreq = WRecObserve(position=(0, 0), response_queue=player.input_queue)
        result = await player._world_request(wreq, WResObserve)
        player.world_input_queue.put.assert_awaited_once_with(wreq)
        player.input_queue.get.assert_awaited_once()
        player.input_queue.task_done.assert_called_once()
        return result

    result = asyncio.run(_run())
    assert isinstance(result, WResObserve)


def test_world_request_raises_on_wrong_type(player: Player) -> None:
    """_world_request must raise TypeError when the response type does not match."""

    async def _run() -> None:
        wrong = WResError(status=WResStatus.ERROR, message="oops")
        player.world_input_queue.put = AsyncMock()
        player.input_queue.get = AsyncMock(return_value=wrong)
        player.input_queue.task_done = MagicMock()

        wreq = WRecObserve(position=(0, 0), response_queue=player.input_queue)
        with pytest.raises(TypeError, match="WResObserve"):
            await player._world_request(wreq, WResObserve)

    asyncio.run(_run())


def test_world_request_stamps_player_name_and_turn(player: Player) -> None:
    """_world_request must stamp its own name and current turn onto the outgoing request."""

    async def _run() -> None:
        obs = WResObserve(
            status=WResStatus.SUCCESS,
            observation=WorldMapObservation.from_position((0, 0)),
        )
        player.world_input_queue.put = AsyncMock()
        player.input_queue.get = AsyncMock(return_value=obs)
        player.input_queue.task_done = MagicMock()
        player.turn = 7

        wreq = WRecObserve(position=(0, 0), response_queue=player.input_queue)
        await player._world_request(wreq, WResObserve)

        assert wreq.player_name == player.name
        assert wreq.turn == 7

    asyncio.run(_run())


def test_world_request_logs_world_response_with_player_and_turn(player: Player) -> None:
    """_world_request must emit EVT_WORLD_RESPONSE with player, turn, kind, and status."""

    async def _run() -> None:
        obs = WResObserve(
            status=WResStatus.SUCCESS,
            observation=WorldMapObservation.from_position((0, 0)),
        )
        player.world_input_queue.put = AsyncMock()
        player.input_queue.get = AsyncMock(return_value=obs)
        player.input_queue.task_done = MagicMock()
        player.turn = 3

        wreq = WRecObserve(position=(0, 0), response_queue=player.input_queue)
        with patch("laife.entities.player.slog") as mock_slog:
            await player._world_request(wreq, WResObserve)

        mock_slog.bind.assert_called_once_with(
            event=EVT_WORLD_RESPONSE,
            player=player.name,
            turn=3,
            kind="WResObserve",
            status=WResStatus.SUCCESS.value,
        )
        mock_slog.bind.return_value.info.assert_called_once_with(EVT_WORLD_RESPONSE)

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# play() - turn counter
# ---------------------------------------------------------------------------


class _StopPlayError(Exception):
    """Sentinel raised to break out of Player.play()'s infinite loop in tests."""


def test_turn_starts_at_zero(player: Player) -> None:
    """A freshly constructed player starts at turn 0."""
    assert player.turn == 0


def test_play_increments_turn_each_iteration(player: Player) -> None:
    """Turn increments by exactly one per play() loop iteration."""

    async def _run() -> None:
        obs = WResObserve(
            status=WResStatus.SUCCESS,
            observation=WorldMapObservation.from_position((0, 0)),
        )
        player.world_input_queue.put = AsyncMock()
        player.input_queue.get = AsyncMock(return_value=obs)
        player.input_queue.task_done = MagicMock()

        # distance=0 makes move() a no-op world-request-wise, isolating the
        # test to the turn counter without needing to mock move collisions.
        move_action = ActionMove(reason="x", direction=CardinalDirection.East, distance=0)
        call_count = 0

        async def _fake_think(*_args: object, **_kwargs: object) -> ActionMove:
            nonlocal call_count
            call_count += 1
            if call_count == 4:
                raise _StopPlayError
            return move_action

        player.brain.think = _fake_think

        with pytest.raises(_StopPlayError):
            await player.play()

    asyncio.run(_run())
    assert player.turn == 4
