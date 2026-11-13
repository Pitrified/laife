"""Tests for PlayerBrainConfig and PlayerBrain.

Each test replaces one chain with a mock and checks both what the chain
receives and what the brain returns, so a chain that starts reading a new
input is caught here.
"""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from llm_core.prompts.prompt_loader import PromptLoaderConfig
import pytest

from laife.entities.action import ActionMove
from laife.entities.action import ActionPickerInput
from laife.entities.utils.directions import CardinalDirection
from laife.entities.world_map_observation import WorldMapObservation
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionStatus
from laife.llm.mission_generator import MissionGeneratorResult
from laife.llm.player_brain import PlayerBrain
from laife.llm.player_brain import PlayerBrainConfig
from laife.llm.player_planner import PlayerPlannerResult
from laife.llm.player_replier import PlayerReplyInput
from laife.llm.player_replier import PlayerReplyOutput
from laife.llm.scripted_chat import ScriptedChatConfig
from laife.params.laife_params import get_laife_params

INVENTORY = "Empty - no utensils carried."


@pytest.fixture
def brain_config() -> PlayerBrainConfig:
    """PlayerBrainConfig on the game's own prompts and a scripted chat config."""
    prompts_fol = get_laife_params().paths.prompts_fol
    return PlayerBrainConfig(
        chat_config=ScriptedChatConfig(),
        action_prompt=PromptLoaderConfig(base_prompt_fol=prompts_fol, prompt_name="player_brain"),
        plan_prompt=PromptLoaderConfig(base_prompt_fol=prompts_fol, prompt_name="player_planner"),
        reply_prompt=PromptLoaderConfig(base_prompt_fol=prompts_fol, prompt_name="player_reply"),
        mission_prompt=PromptLoaderConfig(
            base_prompt_fol=prompts_fol, prompt_name="mission_generator"
        ),
    )


@pytest.fixture
def brain(brain_config: PlayerBrainConfig) -> PlayerBrain:
    """PlayerBrain built from config (no LLM calls made during construction)."""
    return PlayerBrain(brain_config, player_name="tester")


@pytest.fixture
def mission() -> Mission:
    """Return an active mission."""
    return Mission(objective="Build a house", status=MissionStatus.ACTIVE)


@pytest.fixture
def history() -> MissionHistory:
    """Return an empty mission history."""
    return MissionHistory()


@pytest.fixture
def observation() -> WorldMapObservation:
    """Return an observation at the origin."""
    return WorldMapObservation.from_position((0, 0))


def test_brain_builds_its_chains_on_one_config(brain: PlayerBrain) -> None:
    """All four chains take the brain's chat config."""
    config = brain.config.chat_config
    assert brain.action_picker.chat_config is config
    assert brain.planner.config.chat_config is config
    assert brain.replier.config.chat_config is config
    assert brain.mission_generator.config.chat_config is config


# ---------------------------------------------------------------------------
# next_action
# ---------------------------------------------------------------------------


def test_next_action(
    brain: PlayerBrain,
    mission: Mission,
    history: MissionHistory,
    observation: WorldMapObservation,
) -> None:
    """next_action() sends the serialised context and returns the picked action."""
    expected = ActionMove(reason="north", direction=CardinalDirection.North, distance=5)
    brain.action_picker = MagicMock()
    brain.action_picker.ainvoke = AsyncMock(return_value=expected)

    result = asyncio.run(
        brain.next_action(
            mission=mission,
            history=history,
            observation=observation,
            player_state="(10, 20)",
            inventory=INVENTORY,
            turn=3,
        )
    )

    assert result is expected
    brain.action_picker.ainvoke.assert_awaited_once_with(
        ActionPickerInput(
            mission=mission.to_prompt(),
            history=history.to_prompt(),
            observation=observation.to_prompt(),
            player_state="(10, 20)",
            inventory=INVENTORY,
            nearby_players=observation.nearby_players_to_prompt(),
        )
    )


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------


def test_plan(
    brain: PlayerBrain,
    mission: Mission,
    history: MissionHistory,
    observation: WorldMapObservation,
) -> None:
    """plan() forwards the context to the planner and returns its result."""
    expected = PlayerPlannerResult(sub_missions=["Gather wood"], reason="first step")
    brain.planner = MagicMock()
    brain.planner.ainvoke = AsyncMock(return_value=expected)

    result = asyncio.run(
        brain.plan(
            mission=mission,
            history=history,
            observation=observation,
            player_state="(0, 0)",
            turn=3,
        )
    )

    assert result is expected
    brain.planner.ainvoke.assert_awaited_once_with(
        mission=mission,
        history=history,
        observation=observation,
        player_state="(0, 0)",
    )


# ---------------------------------------------------------------------------
# propose_mission
# ---------------------------------------------------------------------------


def test_propose_mission(brain: PlayerBrain, observation: WorldMapObservation) -> None:
    """propose_mission() forwards the context to the generator and returns its result."""
    expected = MissionGeneratorResult(objective="Find water", reason="thirsty")
    brain.mission_generator = MagicMock()
    brain.mission_generator.ainvoke = AsyncMock(return_value=expected)

    result = asyncio.run(
        brain.propose_mission(
            observation=observation,
            player_state="(0, 0)",
            inventory=INVENTORY,
            turn=3,
        )
    )

    assert result is expected
    brain.mission_generator.ainvoke.assert_awaited_once_with(
        observation=observation,
        player_state="(0, 0)",
        inventory=INVENTORY,
    )


# ---------------------------------------------------------------------------
# reply
# ---------------------------------------------------------------------------


def test_reply(brain: PlayerBrain, mission: Mission, history: MissionHistory) -> None:
    """reply() sends the message and own context, and returns the reply text."""
    brain.replier = MagicMock()
    brain.replier.ainvoke = AsyncMock(return_value=PlayerReplyOutput(reply="Sure."))

    result = asyncio.run(
        brain.reply(
            sender_name="bob",
            sender_prompt="Name: bob",
            message="Help?",
            player_state="(0, 0)",
            mission=mission,
            history=history,
            turn=3,
        )
    )

    assert result == "Sure."
    brain.replier.ainvoke.assert_awaited_once_with(
        PlayerReplyInput(
            sender_name="bob",
            sender_prompt="Name: bob",
            message="Help?",
            own_state="(0, 0)",
            own_mission=mission.to_prompt(),
            own_history=history.to_prompt(),
        )
    )


# ---------------------------------------------------------------------------
# timing: one llm_call record per method, labelled by stage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "chain", "stage"),
    [
        ("next_action", "action_picker", "action"),
        ("plan", "planner", "plan"),
        ("propose_mission", "mission_generator", "mission"),
        ("reply", "replier", "reply"),
    ],
)
def test_each_call_is_timed(
    brain: PlayerBrain,
    mission: Mission,
    history: MissionHistory,
    observation: WorldMapObservation,
    method: str,
    chain: str,
    stage: str,
) -> None:
    """Each method times its chain call with its stage, the player name and the turn."""
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value=MagicMock())
    setattr(brain, chain, mock_chain)
    kwargs = {
        "next_action": {
            "mission": mission,
            "history": history,
            "observation": observation,
            "player_state": "",
            "inventory": INVENTORY,
        },
        "plan": {
            "mission": mission,
            "history": history,
            "observation": observation,
            "player_state": "",
        },
        "propose_mission": {"observation": observation, "player_state": "", "inventory": INVENTORY},
        "reply": {
            "sender_name": "bob",
            "sender_prompt": "",
            "message": "hi",
            "player_state": "",
            "mission": mission,
            "history": history,
        },
    }[method]

    with patch("laife.llm.player_brain.timed_llm_call") as mock_timed:
        asyncio.run(getattr(brain, method)(**kwargs, turn=7))

    mock_timed.assert_called_once_with(player="tester", turn=7, model="scripted", stage=stage)
