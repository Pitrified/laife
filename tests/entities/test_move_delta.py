"""Tests for the move delta loop."""

import asyncio
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from laife.config.types import Position
from laife.entities.action import ActionMove
from laife.entities.building import Building
from laife.entities.building import BuildingType
from laife.entities.player import Player
from laife.entities.utils.directions import CardinalDirection
from laife.entities.utils.directions import cardinal_to_delta
from laife.entities.world_channel import WResMove
from laife.entities.world_channel import WResStatus
from laife.entities.world_runner import WorldRunner

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_player(runner: WorldRunner, position: Position = (0, 0)) -> Player:
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
            position=position,
            player_type="hero",
            world_input_queue=runner.input_queue,
        )
    runner.add_player(player)
    return player


def _make_building(position: Position, size: tuple[int, int] = (1, 1)) -> Building:
    bt = BuildingType(building_type="wall", description="A wall", size=size)
    return Building(name="wall", building_type=bt, position=position)


async def _run_move(runner: WorldRunner, player: Player, action: ActionMove) -> WResMove:
    """Drive world simulation + player.move concurrently; return the move result."""
    sim = asyncio.create_task(runner.simulate())
    result = await player.move(action)
    sim.cancel()
    return result


# ---------------------------------------------------------------------------
# cardinal_to_delta - pure unit tests, no world needed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        (CardinalDirection.North, (0, -1)),
        (CardinalDirection.South, (0, 1)),
        (CardinalDirection.East, (1, 0)),
        (CardinalDirection.West, (-1, 0)),
        (CardinalDirection.NorthEast, (1, -1)),
        (CardinalDirection.NorthWest, (-1, -1)),
        (CardinalDirection.SouthEast, (1, 1)),
        (CardinalDirection.SouthWest, (-1, 1)),
    ],
)
def test_cardinal_to_delta_all_directions(
    direction: CardinalDirection,
    expected: tuple[int, int],
) -> None:
    """Each direction maps to the correct unit (dx, dy)."""
    assert cardinal_to_delta(direction) == expected


def test_cardinal_to_delta_step_scaling() -> None:
    """The step parameter scales the delta correctly."""
    assert cardinal_to_delta(CardinalDirection.East, step=3) == (3, 0)
    assert cardinal_to_delta(CardinalDirection.North, step=5) == (0, -5)


# ---------------------------------------------------------------------------
# Move delta loop - async, uses real WorldRunner
# ---------------------------------------------------------------------------


def test_move_free_path() -> None:
    """Player moves the full requested distance when no obstacles are present."""

    async def _run() -> None:
        runner = WorldRunner()
        player = _make_player(runner, position=(0, 0))
        action = ActionMove(direction=CardinalDirection.East, distance=3, reason="going east")
        wrsp = await _run_move(runner, player, action)
        assert wrsp.status == WResStatus.SUCCESS
        assert player.position == (3, 0)

    asyncio.run(_run())


def test_move_blocked_immediately() -> None:
    """Player blocked on the very first step; position does not change."""

    async def _run() -> None:
        runner = WorldRunner()
        runner.buildings.append(_make_building(position=(1, 0)))
        player = _make_player(runner, position=(0, 0))
        action = ActionMove(direction=CardinalDirection.East, distance=3, reason="going east")
        wrsp = await _run_move(runner, player, action)
        assert wrsp.status == WResStatus.ERROR
        assert player.position == (0, 0)

    asyncio.run(_run())


def test_move_blocked_mid_path() -> None:
    """Player advances one step before being blocked; position reflects partial progress."""

    async def _run() -> None:
        runner = WorldRunner()
        runner.buildings.append(_make_building(position=(2, 0)))
        player = _make_player(runner, position=(0, 0))
        action = ActionMove(direction=CardinalDirection.East, distance=3, reason="going east")
        wrsp = await _run_move(runner, player, action)
        assert wrsp.status == WResStatus.ERROR
        assert player.position == (1, 0)

    asyncio.run(_run())


def test_move_feedback_message() -> None:
    """Collision WRes message contains 'Blocked' and 'Obstacle'."""

    async def _run() -> None:
        runner = WorldRunner()
        runner.buildings.append(_make_building(position=(1, 0)))
        player = _make_player(runner, position=(0, 0))
        action = ActionMove(direction=CardinalDirection.East, distance=3, reason="going east")
        wrsp = await _run_move(runner, player, action)
        assert "Blocked" in wrsp.message
        assert "Obstacle" in wrsp.message

    asyncio.run(_run())
