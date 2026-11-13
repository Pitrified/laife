"""Tests for Player.plan()."""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from laife.entities.action import ActionMove
from laife.entities.action import ActionPlan
from laife.entities.player import Player
from laife.entities.player import PlayerState
from laife.entities.utils.directions import CardinalDirection
from laife.entities.world_channel import WResStatus
from laife.entities.world_map_observation import WorldMapObservation
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionHistoryEntry
from laife.llm.mission import MissionStatus
from laife.llm.player_planner import PlayerPlannerResult


@pytest.fixture
def stubbed_player() -> Player:
    """Minimal Player-like object constructed without __init__ for unit testing."""
    player: Player = object.__new__(Player)
    player.name = "tester"
    player.position = (0, 0)
    player.state = PlayerState.IDLE
    player.mission = Mission(objective="Build a house", status=MissionStatus.ACTIVE)
    player.history = MissionHistory()
    player.last_observation = WorldMapObservation.from_position((0, 0))
    player.brain = MagicMock()
    player.turn = 0
    return player


# ---------------------------------------------------------------------------
# Player.plan() integration
# ---------------------------------------------------------------------------


def test_plan_handler_adds_sub_missions(stubbed_player: Player) -> None:
    """Player.plan() must write each sub-mission into the mission tree."""
    sub_missions = ["Gather wood", "Craft axe", "Build wall"]
    stubbed_player.brain.plan = AsyncMock(
        return_value=PlayerPlannerResult(
            sub_missions=sub_missions,
            reason="Step by step.",
        )
    )

    asyncio.run(stubbed_player.plan(ActionPlan(reason="Too complex")))

    assert [s.objective for s in stubbed_player.mission.steps] == sub_missions


def test_plan_handler_resets_history(stubbed_player: Player) -> None:
    """Player.plan() must reset mission history so the next think() starts clean."""
    stubbed_player.history.add_history_entry(
        MissionHistoryEntry(
            action=ActionMove(reason="test", direction=CardinalDirection.North, distance=1),
            result="ok",
        )
    )
    stubbed_player.brain.plan = AsyncMock(
        return_value=PlayerPlannerResult(
            sub_missions=["Do something"],
            reason="Replanning.",
        )
    )

    asyncio.run(stubbed_player.plan(ActionPlan(reason="Stuck")))

    assert stubbed_player.history.history == []


def test_plan_handler_returns_success(stubbed_player: Player) -> None:
    """Player.plan() must return WResPlan(SUCCESS, ...) after planning."""
    stubbed_player.brain.plan = AsyncMock(
        return_value=PlayerPlannerResult(
            sub_missions=["Sub 1"],
            reason="One thing at a time.",
        )
    )

    wrsp = asyncio.run(stubbed_player.plan(ActionPlan(reason="Needs plan")))

    assert wrsp.status == WResStatus.SUCCESS
    assert wrsp.sub_missions == ["Sub 1"]
    assert wrsp.reason == "One thing at a time."
