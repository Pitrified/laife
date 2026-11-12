"""Tests for the scripted chat model."""

import asyncio

from llm_core.chains.structured_chain import StructuredLLMChain
import pytest

from laife.entities.action import ActionEnvelope
from laife.entities.action import ActionInteract
from laife.entities.action import ActionPlan
from laife.entities.player import Player
from laife.entities.world_judge import WorldJudgeResult
from laife.entities.world_runner import WorldRunner
from laife.llm.mission_generator import MissionGeneratorResult
from laife.llm.player_planner import PlayerPlannerResult
from laife.llm.player_replier import PlayerReplyInput
from laife.llm.player_replier import PlayerReplyOutput
from laife.llm.scripted_chat import EmptyScriptError
from laife.llm.scripted_chat import ScriptedChatConfig
from laife.llm.scripted_chat import ScriptedChatModel
from laife.llm.scripted_chat import UnscriptedSchemaError
from laife.llm.scripted_chat import default_script


@pytest.mark.parametrize(
    "schema",
    [
        ActionEnvelope,
        WorldJudgeResult,
        MissionGeneratorResult,
        PlayerPlannerResult,
        PlayerReplyOutput,
    ],
)
def test_every_game_schema_is_answered(schema: type) -> None:
    """Each output model the game's chains ask for gets a valid instance."""
    model = ScriptedChatModel(script=default_script("p1"))
    assert isinstance(model.answer(schema), schema)


def test_script_cycles() -> None:
    """The brain gets the script in order and starts over at the end."""
    script = default_script("p1")
    model = ScriptedChatModel(script=script)
    got = [model.answer(ActionEnvelope).act for _ in range(len(script) + 1)]  # type: ignore[attr-defined]
    assert [type(a) for a in got[: len(script)]] == [type(a) for a in script]
    assert isinstance(got[-1], ActionPlan)


def test_default_script_targets_other_player() -> None:
    """The interaction in the default script addresses the named player."""
    interacts = [a for a in default_script("p1") if isinstance(a, ActionInteract)]
    assert [a.target_name for a in interacts] == ["p1"]


def test_unknown_schema_raises() -> None:
    """An output model with no scripted answer fails by name."""
    model = ScriptedChatModel(script=[])
    with pytest.raises(UnscriptedSchemaError):
        model.answer(PlayerReplyInput)


def test_empty_script_raises_on_action() -> None:
    """A model with no script cannot pick an action."""
    model = ScriptedChatModel(script=[])
    with pytest.raises(EmptyScriptError):
        model.answer(ActionEnvelope)


def test_answers_through_structured_chain() -> None:
    """A real StructuredLLMChain built from the config returns the scripted value."""
    chain = StructuredLLMChain(
        chat_config=ScriptedChatConfig(),
        prompt_str=(
            "{{ sender_name }} {{ sender_prompt }} {{ message }}"
            " {{ own_state }} {{ own_mission }} {{ own_history }}"
        ),
        input_model=PlayerReplyInput,
        output_model=PlayerReplyOutput,
    )
    reply_input = PlayerReplyInput(
        sender_name="p0",
        sender_prompt="",
        message="hi",
        own_state="",
        own_mission="",
        own_history="",
    )
    result = asyncio.run(chain.ainvoke(reply_input))
    assert isinstance(result, PlayerReplyOutput)


def test_runner_judges_take_the_given_config() -> None:
    """WorldRunner(chat_config=...) feeds its judges that config."""
    config = ScriptedChatConfig()
    runner = WorldRunner(chat_config=config)
    assert runner.build_judge.chat_config is config


def test_player_chains_take_the_given_config() -> None:
    """Player(chat_config=...) feeds all four of its chains that config."""
    config = ScriptedChatConfig(script=default_script("p1"))
    player = Player(
        "p0",
        position=(0, 0),
        player_type="inu",
        world_input_queue=WorldRunner().input_queue,
        chat_config=config,
    )
    configs = [
        player.brain.config.chat_config,
        player.planner.config.chat_config,
        player.replier.config.chat_config,
        player.mission_generator.config.chat_config,
    ]
    assert all(c is config for c in configs)
