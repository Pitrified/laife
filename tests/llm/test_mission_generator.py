"""Tests for MissionGeneratorConfig, MissionGenerator."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from laife.entities.world_map_observation import WorldMapObservation
from laife.llm.mission_generator import MissionGenerator
from laife.llm.mission_generator import MissionGeneratorConfig
from laife.llm.mission_generator import MissionGeneratorInput
from laife.llm.mission_generator import MissionGeneratorResult
from laife.llm.prompt_loader import PromptLoaderConfig
from laife.llm.structured_chain import MissingPromptVariablesError
from laife.llm_services.chat.config.ollama import OllamaChatConfig

# ---------------------------------------------------------------------------
# Constants / shared helpers
# ---------------------------------------------------------------------------

VALID_PROMPT = (
    "Observation: {{ observation }}\nState: {{ player_state }}\nInventory: {{ inventory }}\n"
)

INCOMPLETE_PROMPT = "Observation: {{ observation }}\n"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    """Temp directory containing a single v1.jinja with all required variables."""
    d = tmp_path / "mission_generator"
    d.mkdir()
    (d / "v1.jinja").write_text(VALID_PROMPT, encoding="utf-8")
    return tmp_path


@pytest.fixture
def generator_config(prompt_dir: Path) -> MissionGeneratorConfig:
    """MissionGeneratorConfig backed by OllamaChatConfig and a temp prompt dir."""
    return MissionGeneratorConfig(
        chat_config=OllamaChatConfig(),
        prompt_loader_config=PromptLoaderConfig(
            base_prompt_fol=prompt_dir,
            prompt_name="mission_generator",
        ),
    )


@pytest.fixture
def generator(generator_config: MissionGeneratorConfig) -> MissionGenerator:
    """MissionGenerator with __post_init__ patched to skip LLM initialisation."""
    with patch(
        "laife.llm.mission_generator.MissionGenerator.__post_init__",
        lambda self: setattr(self, "_chain", MagicMock()),
    ):
        return MissionGenerator(config=generator_config)


# ---------------------------------------------------------------------------
# MissionGeneratorConfig
# ---------------------------------------------------------------------------


def test_generator_config_instantiation(generator_config: MissionGeneratorConfig) -> None:
    """MissionGeneratorConfig should hold the chat and prompt_loader configs."""
    assert isinstance(generator_config.chat_config, OllamaChatConfig)
    assert generator_config.prompt_loader_config.prompt_name == "mission_generator"


# ---------------------------------------------------------------------------
# MissionGeneratorInput
# ---------------------------------------------------------------------------


def test_generator_input_fields() -> None:
    """MissionGeneratorInput should expose the three required template fields."""
    inp = MissionGeneratorInput(
        observation="A forest to the north.",
        player_state="idle at (0, 0)",
        inventory="Empty - no utensils carried.",
    )
    assert inp.observation == "A forest to the north."
    assert inp.player_state == "idle at (0, 0)"
    assert inp.inventory == "Empty - no utensils carried."


# ---------------------------------------------------------------------------
# MissionGenerator construction
# ---------------------------------------------------------------------------


def test_generator_construction_valid_prompt(prompt_dir: Path) -> None:
    """MissionGenerator should construct without error given a complete prompt."""
    config = MissionGeneratorConfig(
        chat_config=OllamaChatConfig(),
        prompt_loader_config=PromptLoaderConfig(
            base_prompt_fol=prompt_dir,
            prompt_name="mission_generator",
        ),
    )
    with patch(
        "laife.llm.mission_generator.StructuredLLMChain.__post_init__",
        lambda _: None,
    ):
        gen = MissionGenerator(config=config)
    assert gen.config is config


def test_generator_construction_missing_variable(tmp_path: Path) -> None:
    """MissionGenerator should raise MissingPromptVariablesError for an incomplete prompt."""
    d = tmp_path / "mission_generator"
    d.mkdir()
    (d / "v1.jinja").write_text(INCOMPLETE_PROMPT, encoding="utf-8")
    config = MissionGeneratorConfig(
        chat_config=OllamaChatConfig(),
        prompt_loader_config=PromptLoaderConfig(
            base_prompt_fol=tmp_path,
            prompt_name="mission_generator",
        ),
    )
    with pytest.raises(MissingPromptVariablesError):
        MissionGenerator(config=config)


# ---------------------------------------------------------------------------
# MissionGenerator.ainvoke
# ---------------------------------------------------------------------------


def test_generator_ainvoke_returns_result(generator: MissionGenerator) -> None:
    """The ainvoke method returns a MissionGeneratorResult from the underlying chain."""
    expected = MissionGeneratorResult(
        objective="Build a shelter near the lake",
        reason="Player needs protection from the environment.",
    )
    generator._chain.ainvoke = AsyncMock(return_value=expected)
    obs = WorldMapObservation.from_position((3, 4))
    result = asyncio.run(
        generator.ainvoke(
            observation=obs,
            player_state="idle at (3, 4)",
            inventory="Empty - no utensils carried.",
        )
    )
    assert result.objective == "Build a shelter near the lake"
    assert "lake" in result.objective


def test_generator_ainvoke_passes_correct_input(generator: MissionGenerator) -> None:
    """The ainvoke method forwards the correct MissionGeneratorInput to the chain."""
    captured: list[MissionGeneratorInput] = []

    async def recording_ainvoke(chain_input: MissionGeneratorInput) -> MissionGeneratorResult:
        captured.append(chain_input)
        return MissionGeneratorResult(objective="Gather wood", reason="Nearby trees.")

    generator._chain.ainvoke = recording_ainvoke
    obs = WorldMapObservation.from_position((1, 2))
    asyncio.run(
        generator.ainvoke(
            observation=obs,
            player_state="idle at (1, 2)",
            inventory="Empty - no utensils carried.",
        )
    )
    assert len(captured) == 1
    assert captured[0].player_state == "idle at (1, 2)"
    assert captured[0].inventory == "Empty - no utensils carried."
