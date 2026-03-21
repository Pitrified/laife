"""Tests for PlayerBrainConfig and PlayerBrain."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from llm_core.chat.config.ollama import OllamaChatConfig
from llm_core.prompts.prompt_loader import PromptLoaderConfig
import pytest

from laife.entities.action import ActionMove
from laife.entities.action import ActionPickerInput
from laife.entities.utils.directions import CardinalDirection
from laife.entities.world_map_observation import WorldMapObservation
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionStatus
from laife.llm.player_brain import PlayerBrain
from laife.llm.player_brain import PlayerBrainConfig

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

VALID_PROMPT = (
    "Mission: {{ mission }}\n"
    "History: {{ history }}\n"
    "Observation: {{ observation }}\n"
    "State: {{ player_state }}\n"
    "Inventory: {{ inventory }}\n"
)


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    """Temp directory containing a single v1.jinja with all required variables."""
    d = tmp_path / "player_brain"
    d.mkdir()
    (d / "v1.jinja").write_text(VALID_PROMPT, encoding="utf-8")
    return tmp_path


@pytest.fixture
def brain_config(prompt_dir: Path) -> PlayerBrainConfig:
    """PlayerBrainConfig backed by OllamaChatConfig and a temp prompt dir."""
    return PlayerBrainConfig(
        chat_config=OllamaChatConfig(),
        prompt_loader_config=PromptLoaderConfig(
            base_prompt_fol=prompt_dir,
            prompt_name="player_brain",
        ),
    )


# ---------------------------------------------------------------------------
# PlayerBrainConfig
# ---------------------------------------------------------------------------


def test_player_brain_config_instantiation(brain_config: PlayerBrainConfig) -> None:
    """PlayerBrainConfig should hold the chat and prompt_loader configs."""
    assert brain_config.chat_config is not None
    assert brain_config.prompt_loader_config.prompt_name == "player_brain"
    assert brain_config.prompt_loader_config.version == "auto"


# ---------------------------------------------------------------------------
# tests PlayerBrain.think()
# ---------------------------------------------------------------------------


@pytest.fixture
def brain(brain_config: PlayerBrainConfig) -> PlayerBrain:
    """PlayerBrain built from config (no LLM calls made during construction)."""
    return PlayerBrain(brain_config)


def test_think_returns_action_from_picker(brain: PlayerBrain) -> None:
    """think() should delegate to action_picker.ainvoke and return its result."""
    expected_action = ActionMove(
        reason="heading north",
        direction=CardinalDirection.North,
        distance=5,
    )
    brain.action_picker = MagicMock()
    brain.action_picker.ainvoke = AsyncMock(return_value=expected_action)

    result = asyncio.run(
        brain.think(
            mission=Mission(objective="Build a house", status=MissionStatus.ACTIVE),
            history=MissionHistory(),
            observation=WorldMapObservation.from_position((0, 0)),
            player_state="(10, 20)",
            inventory="Empty - no utensils carried.",
        )
    )

    assert result is expected_action
    brain.action_picker.ainvoke.assert_awaited_once()


def test_think_passes_correct_kwargs(brain: PlayerBrain) -> None:
    """think() should forward serialised mission/history/observation/player_state."""
    expected_action = ActionMove(
        reason="test",
        direction=CardinalDirection.South,
        distance=1,
    )
    brain.action_picker = MagicMock()
    brain.action_picker.ainvoke = AsyncMock(return_value=expected_action)

    mission = Mission(objective="Survive", status=MissionStatus.ACTIVE)
    history = MissionHistory()
    observation = WorldMapObservation.from_position((0, 0))
    player_state = "(0, 0)"

    asyncio.run(
        brain.think(
            mission=mission,
            history=history,
            observation=observation,
            player_state=player_state,
            inventory="Empty - no utensils carried.",
        )
    )

    brain.action_picker.ainvoke.assert_awaited_once_with(
        ActionPickerInput(
            mission=mission.to_prompt(),
            history=history.to_prompt(),
            observation=observation.to_prompt(),
            player_state=player_state,
            inventory="Empty - no utensils carried.",
        )
    )
