"""Unit tests for WorldActionJudge and related types."""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from laife.entities.building import Building
from laife.entities.building import BuildingType
from laife.entities.world_channel import WRecBuild
from laife.entities.world_channel import WRecCraft
from laife.entities.world_channel import WResStatus
from laife.entities.world_judge import _REQUIRED_PROMPT_VARS
from laife.entities.world_judge import MissingPromptVariablesError
from laife.entities.world_judge import WorldActionJudge
from laife.entities.world_judge import WorldJudgeInput
from laife.entities.world_judge import WorldJudgeResult
from laife.llm_services.chat.config.ollama import OllamaChatConfig

# ---------------------------------------------------------------------------
# Shared fixtures / constants
# ---------------------------------------------------------------------------

VALID_PROMPT = (
    "Action: {{ action_type }}\n"
    "Details: {{ action_details }}\n"
    "Observation: {{ observation }}\n"
    "State: {{ player_state }}\n"
)

INCOMPLETE_PROMPT = "Action: {{ action_type }}\n"


@pytest.fixture
def chat_config() -> OllamaChatConfig:
    """OllamaChatConfig for use in tests (no real LLM calls made)."""
    return OllamaChatConfig()


@pytest.fixture
def judge(chat_config: OllamaChatConfig) -> WorldActionJudge:
    """WorldActionJudge with __post_init__ patched to avoid LLM initialisation."""
    with patch(
        "laife.entities.world_judge.WorldActionJudge.__post_init__",
        lambda self: setattr(self, "chain", MagicMock()),
    ):
        return WorldActionJudge(chat_config=chat_config, prompt_str=VALID_PROMPT)


@pytest.fixture
def judge_input() -> WorldJudgeInput:
    """Minimal valid WorldJudgeInput fixture."""
    return WorldJudgeInput(
        action_type="build",
        action_details="building_type=house, size=10",
        observation="Nothing nearby.",
        player_state="Player p0 at (0, 0) - idle",
    )


# ---------------------------------------------------------------------------
# WResStatus.from_bool
# ---------------------------------------------------------------------------


def test_wres_status_from_bool_true() -> None:
    """from_bool(True) must return SUCCESS."""
    assert WResStatus.from_bool(success=True) is WResStatus.SUCCESS


def test_wres_status_from_bool_false() -> None:
    """from_bool(False) must return ERROR."""
    assert WResStatus.from_bool(success=False) is WResStatus.ERROR


# ---------------------------------------------------------------------------
# WorldJudgeInput
# ---------------------------------------------------------------------------


def test_world_judge_input_to_kw(judge_input: WorldJudgeInput) -> None:
    """to_kw() must return all four required fields."""
    kw = judge_input.to_kw()
    assert kw["action_type"] == "build"
    assert kw["action_details"] == "building_type=house, size=10"
    assert kw["observation"] == "Nothing nearby."
    assert kw["player_state"] == "Player p0 at (0, 0) - idle"


def test_world_judge_input_fields_match_required_vars() -> None:
    """WorldJudgeInput fields must equal the _REQUIRED_PROMPT_VARS sentinel."""
    assert frozenset(WorldJudgeInput.model_fields) == _REQUIRED_PROMPT_VARS


# ---------------------------------------------------------------------------
# WorldJudgeResult
# ---------------------------------------------------------------------------


def test_world_judge_result_success() -> None:
    """WorldJudgeResult with success=True must store feedback."""
    result = WorldJudgeResult(success=True, feedback="Build approved.")
    assert result.success is True
    assert result.feedback == "Build approved."


def test_world_judge_result_failure() -> None:
    """WorldJudgeResult with success=False must store feedback."""
    result = WorldJudgeResult(success=False, feedback="No crafting station nearby.")
    assert result.success is False
    assert "crafting station" in result.feedback


# ---------------------------------------------------------------------------
# MissingPromptVariablesError
# ---------------------------------------------------------------------------


def test_missing_prompt_variables_error_message() -> None:
    """MissingPromptVariablesError must list missing variables in its message."""
    err = MissingPromptVariablesError({"observation", "player_state"})
    msg = str(err)
    assert "observation" in msg
    assert "player_state" in msg


# ---------------------------------------------------------------------------
# WorldActionJudge - construction validation
# ---------------------------------------------------------------------------


def test_judge_raises_on_incomplete_prompt(chat_config: OllamaChatConfig) -> None:
    """WorldActionJudge must raise MissingPromptVariablesError if prompt lacks required vars."""
    with pytest.raises(MissingPromptVariablesError):
        WorldActionJudge(chat_config=chat_config, prompt_str=INCOMPLETE_PROMPT)


def test_judge_accepts_valid_prompt(chat_config: OllamaChatConfig) -> None:
    """WorldActionJudge must not raise when all required variables are present."""
    with patch("laife.entities.world_judge.WorldActionJudge.__post_init__", lambda _: None):
        j = WorldActionJudge(chat_config=chat_config, prompt_str=VALID_PROMPT)
    assert j.prompt_str == VALID_PROMPT


# ---------------------------------------------------------------------------
# WorldActionJudge - invoke / ainvoke
# ---------------------------------------------------------------------------


def test_judge_invoke_returns_world_judge_result(
    judge: WorldActionJudge,
    judge_input: WorldJudgeInput,
) -> None:
    """invoke() must return a WorldJudgeResult when chain returns one."""
    expected = WorldJudgeResult(success=True, feedback="Looks good.")
    judge.chain.invoke = MagicMock(return_value=expected)

    result = judge.invoke(judge_input)

    assert isinstance(result, WorldJudgeResult)
    assert result.success is True


def test_judge_invoke_raises_on_wrong_type(
    judge: WorldActionJudge,
    judge_input: WorldJudgeInput,
) -> None:
    """invoke() must raise TypeError when chain returns an unexpected type."""
    judge.chain.invoke = MagicMock(return_value="unexpected string")

    with pytest.raises(TypeError):
        judge.invoke(judge_input)


def test_judge_ainvoke_returns_world_judge_result(
    judge: WorldActionJudge,
    judge_input: WorldJudgeInput,
) -> None:
    """ainvoke() must return a WorldJudgeResult when chain returns one."""
    expected = WorldJudgeResult(success=False, feedback="No station nearby.")
    judge.chain.ainvoke = AsyncMock(return_value=expected)

    result = asyncio.run(judge.ainvoke(judge_input))

    assert isinstance(result, WorldJudgeResult)
    assert result.success is False


def test_judge_ainvoke_raises_on_wrong_type(
    judge: WorldActionJudge,
    judge_input: WorldJudgeInput,
) -> None:
    """ainvoke() must raise TypeError when chain returns an unexpected type."""
    judge.chain.ainvoke = AsyncMock(return_value=42)

    with pytest.raises(TypeError):
        asyncio.run(judge.ainvoke(judge_input))


# ---------------------------------------------------------------------------
# WRecCraft
# ---------------------------------------------------------------------------


def test_wrec_craft_stores_fields() -> None:
    """WRecCraft must store all fields and expose them as attributes."""
    q: asyncio.Queue = asyncio.Queue()
    req = WRecCraft(
        utensil_name="wooden pickaxe",
        description="Crafted from wood and stone.",
        observation="Crafting table nearby.",
        player_state="Player at (5, 5) - idle",
        response_queue=q,
    )

    assert req.utensil_name == "wooden pickaxe"
    assert req.description == "Crafted from wood and stone."
    assert req.observation == "Crafting table nearby."
    assert req.player_state == "Player at (5, 5) - idle"
    assert req.response_queue is q


def test_wrec_craft_str_contains_name() -> None:
    """str(WRecCraft) must include the utensil name."""
    req = WRecCraft(
        utensil_name="forge hammer",
        description="A heavy hammer.",
        observation="",
        player_state="",
        response_queue=asyncio.Queue(),
    )
    assert "forge hammer" in str(req)


# ---------------------------------------------------------------------------
# WRecBuild - new fields
# ---------------------------------------------------------------------------


def test_wrec_build_stores_observation_and_state() -> None:
    """WRecBuild must store observation and player_state alongside the building."""
    bt = BuildingType(building_type="house", description="A house.", size=(10, 10))
    building = Building(name="My House", building_type=bt, position=(0, 0))

    req = WRecBuild(
        building=building,
        observation="Clear area.",
        player_state="Player at (0, 0) - idle",
        response_queue=asyncio.Queue(),
    )

    assert req.building is building
    assert req.observation == "Clear area."
    assert req.player_state == "Player at (0, 0) - idle"
