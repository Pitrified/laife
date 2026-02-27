"""Tests for PlayerPlannerConfig, PlayerPlanner, and Player.plan() integration."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

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
from laife.llm.player_planner import PlayerPlanner
from laife.llm.player_planner import PlayerPlannerConfig
from laife.llm.player_planner import PlayerPlannerInput
from laife.llm.player_planner import PlayerPlannerResult
from laife.llm.prompt_loader import PromptLoaderConfig
from laife.llm.structured_chain import MissingPromptVariablesError
from laife.llm_services.chat.config.ollama import OllamaChatConfig

# ---------------------------------------------------------------------------
# Constants / shared helpers
# ---------------------------------------------------------------------------

VALID_PROMPT = (
    "Mission: {{ mission }}\n"
    "History: {{ history }}\n"
    "Observation: {{ observation }}\n"
    "State: {{ player_state }}\n"
)

INCOMPLETE_PROMPT = "Mission: {{ mission }}\n"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    """Temp directory containing a single v1.jinja with all required variables."""
    d = tmp_path / "player_planner"
    d.mkdir()
    (d / "v1.jinja").write_text(VALID_PROMPT, encoding="utf-8")
    return tmp_path


@pytest.fixture
def planner_config(prompt_dir: Path) -> PlayerPlannerConfig:
    """PlayerPlannerConfig backed by OllamaChatConfig and a temp prompt dir."""
    return PlayerPlannerConfig(
        chat_config=OllamaChatConfig(),
        prompt_loader_config=PromptLoaderConfig(
            base_prompt_fol=prompt_dir,
            prompt_name="player_planner",
        ),
    )


@pytest.fixture
def planner(planner_config: PlayerPlannerConfig) -> PlayerPlanner:
    """PlayerPlanner with __post_init__ patched to avoid LLM initialisation."""
    with patch(
        "laife.llm.player_planner.PlayerPlanner.__post_init__",
        lambda self: setattr(self, "_chain", MagicMock()),
    ):
        return PlayerPlanner(config=planner_config)


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
    player.planner = MagicMock()
    return player


# ---------------------------------------------------------------------------
# PlayerPlannerConfig
# ---------------------------------------------------------------------------


def test_planner_config_instantiation(planner_config: PlayerPlannerConfig) -> None:
    """PlayerPlannerConfig should hold the chat and prompt_loader configs."""
    assert planner_config.chat_config is not None
    assert planner_config.prompt_loader_config.prompt_name == "player_planner"
    assert planner_config.prompt_loader_config.version == "auto"


# ---------------------------------------------------------------------------
# PlayerPlanner construction
# ---------------------------------------------------------------------------


def test_planner_raises_on_missing_prompt_variables(
    prompt_dir: Path,
) -> None:
    """PlayerPlanner.__post_init__ must raise when prompt vars are missing."""
    bad_dir = prompt_dir / "player_planner_bad"
    bad_dir.mkdir()
    (bad_dir / "v1.jinja").write_text(INCOMPLETE_PROMPT, encoding="utf-8")
    config = PlayerPlannerConfig(
        chat_config=OllamaChatConfig(),
        prompt_loader_config=PromptLoaderConfig(
            base_prompt_fol=prompt_dir,
            prompt_name="player_planner_bad",
        ),
    )
    with pytest.raises(MissingPromptVariablesError):
        PlayerPlanner(config=config)


# ---------------------------------------------------------------------------
# PlayerPlanner.ainvoke
# ---------------------------------------------------------------------------


def test_ainvoke_passes_correct_input(planner: PlayerPlanner) -> None:
    """Ainvoke must call _chain.ainvoke with a correctly built PlayerPlannerInput."""
    expected_result = PlayerPlannerResult(
        sub_missions=["Gather wood", "Craft axe"],
        reason="Need tools first.",
    )
    planner._chain = MagicMock()
    planner._chain.ainvoke = AsyncMock(return_value=expected_result)

    mission = Mission(objective="Build a house", status=MissionStatus.ACTIVE)
    history = MissionHistory()
    observation = WorldMapObservation.from_position((0, 0))
    player_state = "tester at (0, 0) - idle"

    asyncio.run(
        planner.ainvoke(
            mission=mission,
            history=history,
            observation=observation,
            player_state=player_state,
        )
    )

    planner._chain.ainvoke.assert_awaited_once_with(
        PlayerPlannerInput(
            mission=mission.to_prompt(),
            history=history.to_prompt(),
            observation=observation.to_prompt(),
            player_state=player_state,
        )
    )


def test_ainvoke_returns_result(planner: PlayerPlanner) -> None:
    """Ainvoke must return the PlayerPlannerResult produced by the chain."""
    expected_result = PlayerPlannerResult(
        sub_missions=["Find a clearing", "Build a wall"],
        reason="Start small.",
    )
    planner._chain = MagicMock()
    planner._chain.ainvoke = AsyncMock(return_value=expected_result)

    result = asyncio.run(
        planner.ainvoke(
            mission=Mission(objective="Build a house", status=MissionStatus.ACTIVE),
            history=MissionHistory(),
            observation=WorldMapObservation.from_position((0, 0)),
            player_state="(0, 0)",
        )
    )

    assert result is expected_result


# ---------------------------------------------------------------------------
# Player.plan() integration
# ---------------------------------------------------------------------------


def test_plan_handler_adds_sub_missions(stubbed_player: Player) -> None:
    """Player.plan() must write each sub-mission into the mission tree."""
    sub_missions = ["Gather wood", "Craft axe", "Build wall"]
    stubbed_player.planner.ainvoke = AsyncMock(
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
    stubbed_player.planner.ainvoke = AsyncMock(
        return_value=PlayerPlannerResult(
            sub_missions=["Do something"],
            reason="Replanning.",
        )
    )

    asyncio.run(stubbed_player.plan(ActionPlan(reason="Stuck")))

    assert stubbed_player.history.history == []


def test_plan_handler_returns_success(stubbed_player: Player) -> None:
    """Player.plan() must return WRes(SUCCESS, ...) after planning."""
    stubbed_player.planner.ainvoke = AsyncMock(
        return_value=PlayerPlannerResult(
            sub_missions=["Sub 1"],
            reason="One thing at a time.",
        )
    )

    wrsp = asyncio.run(stubbed_player.plan(ActionPlan(reason="Needs plan")))

    assert wrsp.status == WResStatus.SUCCESS
    assert "sub_missions" in wrsp.response_data
    assert "reason" in wrsp.response_data
