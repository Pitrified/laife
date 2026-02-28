"""Tests for Player mission lifecycle - completion and failure transitions."""

from collections.abc import Generator
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from laife.entities.action import ActionBuild
from laife.entities.action import ActionCraft
from laife.entities.action import ActionMove
from laife.entities.action import ActionPlan
from laife.entities.player import Player
from laife.entities.utils.directions import CardinalDirection
from laife.entities.world_channel import WResBuild
from laife.entities.world_channel import WResCraft
from laife.entities.world_channel import WResMove
from laife.entities.world_channel import WResStatus
from laife.entities.world_runner import WorldRunner
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionHistoryEntry
from laife.llm.mission import MissionStatus

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
        PromptLoaderConfig=MagicMock(),
        PlayerBrain=MagicMock(return_value=MagicMock()),
        PlayerPlanner=MagicMock(return_value=MagicMock()),
        PlayerReplier=MagicMock(return_value=MagicMock()),
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
    """Prevent alg.log from trying to create asyncio tasks outside an event loop."""
    with patch("laife.entities.player.alg"):
        yield


@pytest.fixture
def player() -> Player:
    """Return a Player connected to a fresh WorldRunner with all LLM mocked."""
    runner = WorldRunner()
    return _make_player(runner)


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
    old_objective = player.mission.objective
    player._start_new_mission()
    assert player.mission.status == MissionStatus.ACTIVE
    assert player.mission.objective == old_objective


def test_start_new_mission_resets_consecutive_failures(player: Player) -> None:
    """The new mission starts with consecutive_failures at zero."""
    player.mission.consecutive_failures = 5
    player.mission.status = MissionStatus.FAILED
    player._start_new_mission()
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
    player._start_new_mission()
    assert isinstance(player.history, MissionHistory)
    assert len(player.history.history) == 0
