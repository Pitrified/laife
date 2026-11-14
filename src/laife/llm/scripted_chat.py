"""The game's script for llm-core's scripted chat model, for running with no provider.

Every chain in the game asks for structured output, so the model answers by
schema: the player brain gets the next action of its script, cycling, and
every other chain gets a fixed value.

Each player builds its own chains, so each player gets its own
:class:`ScriptedChatConfig` carrying its own script; the world's judges get
one with an empty script, since they never ask for an action.
"""

import asyncio
from itertools import cycle
from typing import Any

from langchain_core.runnables import Runnable
from langchain_core.runnables import RunnableLambda
from llm_core.testing.scripted_chat_model import Answers
from llm_core.testing.scripted_chat_model import ScriptedChatConfig as BaseScriptedChatConfig
from llm_core.testing.scripted_chat_model import ScriptedChatModel
from pydantic import BaseModel
from pydantic import Field

from laife.entities.action import ActionBuild
from laife.entities.action import ActionComplete
from laife.entities.action import ActionCraft
from laife.entities.action import ActionEnvelope
from laife.entities.action import ActionInteract
from laife.entities.action import ActionMove
from laife.entities.action import ActionPlan
from laife.entities.action import Actions
from laife.entities.utils.directions import CardinalDirection
from laife.entities.world_judge import WorldJudgeResult
from laife.llm.mission_generator import MissionGeneratorResult
from laife.llm.player_planner import PlayerPlannerResult
from laife.llm.player_replier import PlayerReplyOutput


class EmptyScriptError(Exception):
    """An action was asked of a scripted model whose script is empty."""

    def __init__(self) -> None:
        """Explain where the script comes from."""
        super().__init__(
            "The scripted model was asked for an action but its script is empty;"
            " give the player a ScriptedChatConfig with a script."
        )


def default_script(other_player: str) -> list[Actions]:
    """Return one action of each type, so a cycle walks every branch of the turn loop.

    *other_player* is the target of the interaction.
    """
    return [
        ActionPlan(reason="scripted: split the mission"),
        ActionMove(reason="scripted: walk", direction=CardinalDirection.East, distance=2),
        ActionBuild(
            reason="scripted: build",
            building_type="shed",
            description="A small wooden shed.",
            size=1,
        ),
        ActionCraft(
            reason="scripted: craft",
            utensil_name="hammer",
            description="A wooden hammer.",
        ),
        ActionInteract(
            reason="scripted: talk",
            target_name=other_player,
            message="Hello, how is your mission going?",
        ),
        ActionComplete(reason="scripted: done", outcome="The scripted steps ran."),
    ]


class PacedScriptedChatModel(ScriptedChatModel):
    """llm-core's scripted model, answering async calls after *pace* seconds.

    The delay is an awaited ``asyncio.sleep``: it holds the caller, as a slow
    model would, and the rest of the game runs on. A sync ``invoke`` answers
    at once; the game's chains are awaited.

    Attributes:
        pace: Seconds before each async answer.
    """

    pace: float

    def with_structured_output(
        self,
        schema: type[BaseModel] | dict[str, Any],
        *,
        include_raw: bool = False,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002, ANN401
    ) -> Runnable:
        """Return a runnable answering for *schema*, after the pace when awaited."""

        async def answer_later(_prompt: object) -> BaseModel:
            await asyncio.sleep(self.pace)
            return self.answer(schema)

        return RunnableLambda(lambda _prompt: self.answer(schema), afunc=answer_later)


class ScriptedChatConfig(BaseScriptedChatConfig):
    """llm-core's scripted chat config with the game's answers.

    Each chain builds its own model, and each model gets its own pass through
    the script, so only the brain's action chain advances it.

    Attributes:
        script: The player's actions; empty for the world's judges.
        pace: Seconds each awaited answer takes; 0 answers at once.
    """

    script: list[Actions] = Field(default_factory=list)
    pace: float = 0.0

    def create_chat_model(self) -> ScriptedChatModel:
        """Return a scripted model with fresh answers, paced when *pace* is set."""
        if self.pace <= 0:
            return super().create_chat_model()
        return PacedScriptedChatModel(answers=self.build_answers(), pace=self.pace)

    def build_answers(self) -> Answers:
        """Return the game's answers, with a fresh cycle through the script."""
        actions = cycle(self.script)

        def next_action() -> ActionEnvelope:
            if not self.script:
                raise EmptyScriptError
            return ActionEnvelope(act=next(actions).model_copy())

        return {
            ActionEnvelope: next_action,
            WorldJudgeResult: lambda: WorldJudgeResult(success=True, feedback="scripted: approved"),
            MissionGeneratorResult: lambda: MissionGeneratorResult(
                objective="Build a shed and craft a hammer.",
                reason="scripted: fixed objective",
            ),
            PlayerPlannerResult: lambda: PlayerPlannerResult(
                sub_missions=["Build a shed.", "Craft a hammer."],
                reason="scripted: fixed plan",
            ),
            PlayerReplyOutput: lambda: PlayerReplyOutput(reply="scripted: going well, thanks."),
        }
