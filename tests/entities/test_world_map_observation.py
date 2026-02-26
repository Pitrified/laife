"""Tests for WorldMapObservation and WorldRunner.observe_at."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from laife.config.types import Position
from laife.entities.building import Building
from laife.entities.building import BuildingType
from laife.entities.player import Player
from laife.entities.world_map_observation import NearbyEntity
from laife.entities.world_map_observation import WorldMapObservation
from laife.entities.world_map_observation import euclidean
from laife.entities.world_runner import WorldRunner

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WALL_TYPE = BuildingType(building_type="wall", description="A stone wall.", size=(1, 1))


def _building(name: str, position: Position) -> Building:
    return Building(name=name, building_type=_WALL_TYPE, position=position)


def _make_player(runner: WorldRunner, position: Position = (0, 0)) -> Player:
    """Create a Player with all LLM components mocked out."""
    with patch.multiple(
        "laife.entities.player",
        get_laife_params=MagicMock(return_value=MagicMock()),
        PlayerBrainConfig=MagicMock(),
        PromptLoaderConfig=MagicMock(),
        PlayerBrain=MagicMock(return_value=MagicMock()),
    ):
        player = Player(
            name="tester",
            position=position,
            player_type="hero",
            world_input_queue=runner.input_queue,
        )
    runner.add_player(player)
    return player


# ---------------------------------------------------------------------------
# euclidean helper
# ---------------------------------------------------------------------------


def test_euclidean_same_point() -> None:
    """Distance between identical positions is zero."""
    assert euclidean((0, 0), (0, 0)) == 0.0


def test_euclidean_cardinal() -> None:
    """Distance along axes equals the absolute offset."""
    assert euclidean((0, 0), (3, 0)) == pytest.approx(3.0)
    assert euclidean((0, 0), (0, 4)) == pytest.approx(4.0)


def test_euclidean_diagonal() -> None:
    """Distance on the classic 3-4-5 triangle is 5."""
    assert euclidean((0, 0), (3, 4)) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# WorldMapObservation.from_position
# ---------------------------------------------------------------------------


def test_from_position_creates_empty_observation() -> None:
    """from_position() should produce an observation with no nearby entities."""
    obs = WorldMapObservation.from_position((5, 7))
    assert obs.player_position == (5, 7)
    assert obs.nearby_entities == []
    assert obs.radius == 20


# ---------------------------------------------------------------------------
# WorldMapObservation.to_prompt
# ---------------------------------------------------------------------------


def test_to_prompt_empty() -> None:
    """to_prompt() with no entities reports position and nothing nearby."""
    obs = WorldMapObservation.from_position((10, 5))
    prompt = obs.to_prompt()
    assert "You are at position (10, 5)." in prompt
    assert "Nothing is nearby." in prompt


def test_to_prompt_single_building_east() -> None:
    """to_prompt() names a building east of the observer with correct distance."""
    obs = WorldMapObservation(
        player_position=(0, 0),
        nearby_entities=[
            NearbyEntity(
                entity_type="building",
                name="Woodcutter Hut",
                relative_position=(5, 0),
                distance=5.0,
            )
        ],
    )
    prompt = obs.to_prompt()
    assert 'Building "Woodcutter Hut"' in prompt
    assert "east" in prompt
    assert "5.0" in prompt


def test_to_prompt_single_player_west() -> None:
    """to_prompt() names a player west of the observer with correct distance."""
    obs = WorldMapObservation(
        player_position=(10, 10),
        nearby_entities=[
            NearbyEntity(
                entity_type="player",
                name="Yuki",
                relative_position=(-3, 0),
                distance=3.0,
            )
        ],
    )
    prompt = obs.to_prompt()
    assert 'Player "Yuki"' in prompt
    assert "west" in prompt
    assert "3.0" in prompt


def test_to_prompt_multiple_entities() -> None:
    """to_prompt() lists all nearby entities."""
    obs = WorldMapObservation(
        player_position=(0, 0),
        nearby_entities=[
            NearbyEntity(
                entity_type="building",
                name="Tower",
                relative_position=(0, -4),
                distance=4.0,
            ),
            NearbyEntity(
                entity_type="player",
                name="Koda",
                relative_position=(3, 4),
                distance=5.0,
            ),
        ],
    )
    prompt = obs.to_prompt()
    assert '"Tower"' in prompt
    assert '"Koda"' in prompt
    assert "north" in prompt.lower()


def test_to_prompt_shows_radius() -> None:
    """to_prompt() includes the configured radius in the header line."""
    obs = WorldMapObservation(
        player_position=(0, 0),
        nearby_entities=[
            NearbyEntity(
                entity_type="building",
                name="Barn",
                relative_position=(1, 0),
                distance=1.0,
            )
        ],
        radius=15,
    )
    assert "within 15 tiles" in obs.to_prompt()


# ---------------------------------------------------------------------------
# WorldRunner.observe_at
# ---------------------------------------------------------------------------


def test_observe_at_empty_world() -> None:
    """observe_at() on an empty world returns an observation with no entities."""
    runner = WorldRunner()
    res = runner.observe_at((5, 5))
    obs: WorldMapObservation = res.response_data["observation"]
    assert obs.player_position == (5, 5)
    assert obs.nearby_entities == []


def test_observe_at_includes_building_within_radius() -> None:
    """Buildings within the radius are included in the observation."""
    runner = WorldRunner()
    runner.buildings.append(_building("Barn", (3, 0)))
    res = runner.observe_at((0, 0), radius=10)
    obs: WorldMapObservation = res.response_data["observation"]
    names = [e.name for e in obs.nearby_entities]
    assert "Barn" in names


def test_observe_at_excludes_building_outside_radius() -> None:
    """Buildings further than the radius are excluded from the observation."""
    runner = WorldRunner()
    runner.buildings.append(_building("FarTower", (50, 50)))
    res = runner.observe_at((0, 0), radius=10)
    obs: WorldMapObservation = res.response_data["observation"]
    assert obs.nearby_entities == []


def test_observe_at_skips_player_at_same_position() -> None:
    """The observing player (distance 0) is excluded from the observation."""
    runner = WorldRunner()
    _make_player(runner, position=(0, 0))
    res = runner.observe_at((0, 0), radius=20)
    obs: WorldMapObservation = res.response_data["observation"]
    # The observing player sits at (0,0); it should be excluded
    assert all(e.distance > 0 for e in obs.nearby_entities)


def test_observe_at_includes_other_player() -> None:
    """Other players within the radius appear as player entities."""
    runner = WorldRunner()
    _make_player(runner, position=(0, 0))   # observing player
    _make_player(runner, position=(5, 0))   # other player
    res = runner.observe_at((0, 0), radius=20)
    obs: WorldMapObservation = res.response_data["observation"]
    player_entities = [e for e in obs.nearby_entities if e.entity_type == "player"]
    assert len(player_entities) == 1
    assert player_entities[0].distance == pytest.approx(5.0)


def test_observe_at_relative_positions_are_correct() -> None:
    """relative_position is expressed as (dx, dy) from the observer."""
    runner = WorldRunner()
    runner.buildings.append(_building("East Wall", (10, 0)))
    res = runner.observe_at((5, 0), radius=20)
    obs: WorldMapObservation = res.response_data["observation"]
    entity = obs.nearby_entities[0]
    assert entity.relative_position == (5, 0)
    assert entity.distance == pytest.approx(5.0)


def test_observe_at_distance_correct_diagonal() -> None:
    """Euclidean distance is calculated correctly for diagonal positions."""
    runner = WorldRunner()
    runner.buildings.append(_building("Diagonal", (3, 4)))
    res = runner.observe_at((0, 0), radius=10)
    obs: WorldMapObservation = res.response_data["observation"]
    assert obs.nearby_entities[0].distance == pytest.approx(5.0)
