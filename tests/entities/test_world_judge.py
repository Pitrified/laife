"""Unit tests for WorldJudge, its models and the runner's judged requests."""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from llm_core.prompts.prompt_loader import PromptLoaderConfig
import pytest

from laife.entities.building import Building
from laife.entities.building import BuildingType
from laife.entities.world_channel import WRecBuild
from laife.entities.world_channel import WRecCraft
from laife.entities.world_channel import WResStatus
from laife.entities.world_judge import WorldJudge
from laife.entities.world_judge import WorldJudgeConfig
from laife.entities.world_judge import WorldJudgeInput
from laife.entities.world_judge import WorldJudgeResult
from laife.entities.world_runner import WorldRunner
from laife.llm.scripted_chat import ScriptedChatConfig
from laife.params.laife_params import get_laife_params

# ---------------------------------------------------------------------------
# Shared fixtures / constants
# ---------------------------------------------------------------------------

VERDICT = WorldJudgeResult(success=True, feedback="Fine.")


@pytest.fixture
def judge() -> WorldJudge:
    """WorldJudge on the game's own prompts and a scripted chat config."""
    prompts_fol = get_laife_params().paths.prompts_fol
    return WorldJudge(
        WorldJudgeConfig(
            chat_config=ScriptedChatConfig(),
            build_prompt=PromptLoaderConfig(
                base_prompt_fol=prompts_fol, prompt_name="world_judge_build"
            ),
            craft_prompt=PromptLoaderConfig(
                base_prompt_fol=prompts_fol, prompt_name="world_judge_craft"
            ),
            complete_prompt=PromptLoaderConfig(
                base_prompt_fol=prompts_fol, prompt_name="world_judge_complete"
            ),
        )
    )


def _mock_chain(verdict: WorldJudgeResult = VERDICT) -> MagicMock:
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value=verdict)
    return chain


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


def test_world_judge_input_has_required_fields() -> None:
    """WorldJudgeInput must declare all four prompt-variable fields."""
    assert frozenset(WorldJudgeInput.model_fields) == {
        "action_type",
        "action_details",
        "observation",
        "player_state",
    }


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
# WorldJudge - one chain per judged request, input built from plain values
# ---------------------------------------------------------------------------


def test_judge_builds_its_chains_on_one_config(judge: WorldJudge) -> None:
    """All three chains take the judge's chat config."""
    config = judge.config.chat_config
    assert judge.build_chain.chat_config is config
    assert judge.craft_chain.chat_config is config
    assert judge.complete_chain.chat_config is config


def test_check_build(judge: WorldJudge) -> None:
    """check_build() describes the building to the build chain and returns its verdict."""
    judge.build_chain = _mock_chain()
    building = _build_request((0, 0)).building

    result = asyncio.run(
        judge.check_build(building=building, observation="Clear area.", player_state="idle")
    )

    assert result is VERDICT
    judge.build_chain.ainvoke.assert_awaited_once_with(
        WorldJudgeInput(
            action_type="build",
            action_details="building_type=house, name=New House, size=(10, 10), description=None",
            observation="Clear area.",
            player_state="idle",
        )
    )


def test_check_craft(judge: WorldJudge) -> None:
    """check_craft() describes the utensil to the craft chain and returns its verdict."""
    judge.craft_chain = _mock_chain()

    result = asyncio.run(
        judge.check_craft(
            utensil_name="axe",
            description="Stone head.",
            observation="Rocks nearby.",
            player_state="idle",
        )
    )

    assert result is VERDICT
    judge.craft_chain.ainvoke.assert_awaited_once_with(
        WorldJudgeInput(
            action_type="craft",
            action_details="utensil_name=axe, description=Stone head.",
            observation="Rocks nearby.",
            player_state="idle",
        )
    )


def test_check_complete(judge: WorldJudge) -> None:
    """check_complete() sends objective and outcome to the complete chain."""
    judge.complete_chain = _mock_chain()

    result = asyncio.run(
        judge.check_complete(
            objective="Build a shed",
            outcome="The shed stands.",
            observation="A shed.",
            player_state="idle",
        )
    )

    assert result is VERDICT
    judge.complete_chain.ainvoke.assert_awaited_once_with(
        WorldJudgeInput(
            action_type="complete: Build a shed",
            action_details="The shed stands.",
            observation="A shed.",
            player_state="idle",
        )
    )


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


# ---------------------------------------------------------------------------
# judge_and_build - collision check before the paid judge
# ---------------------------------------------------------------------------


def _build_request(position: tuple[int, int]) -> WRecBuild:
    bt = BuildingType(building_type="house", description="A house.", size=(10, 10))
    return WRecBuild(
        building=Building(name="New House", building_type=bt, position=position),
        observation="Clear area.",
        player_state="Player at (0, 0) - idle",
        response_queue=asyncio.Queue(),
    )


def test_judge_and_build_colliding_skips_judge() -> None:
    """A colliding build returns the collision error without calling the judge."""
    runner = WorldRunner()
    runner.add_building(_build_request((0, 0)).building)
    runner.judge.check_build = AsyncMock()

    res = asyncio.run(runner.judge_and_build(_build_request((5, 5))))

    assert res.status == WResStatus.ERROR
    assert "collides" in res.feedback
    runner.judge.check_build.assert_not_called()
    assert len(runner.buildings) == 1


def test_judge_and_build_free_spot_asks_judge() -> None:
    """A build on a free spot goes through the judge and is added when approved."""
    runner = WorldRunner()
    runner.judge.check_build = AsyncMock(return_value=VERDICT)
    req = _build_request((100, 100))

    res = asyncio.run(runner.judge_and_build(req))

    assert res.status == WResStatus.SUCCESS
    runner.judge.check_build.assert_awaited_once_with(
        building=req.building, observation=req.observation, player_state=req.player_state
    )
    assert runner.buildings == [req.building]
