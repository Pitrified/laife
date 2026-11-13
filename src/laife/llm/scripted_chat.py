"""The game's script for llm-core's scripted chat model, for running with no provider.

Every chain in the game asks for structured output, so the model answers by
schema: the player brain gets the next action of its script, cycling, and
every other chain gets a fixed value.

Each player builds its own chains, so each player gets its own
:class:`ScriptedChatConfig` carrying its own script; the world's judges get
one with an empty script, since they never ask for an action.
"""

from itertools import cycle

from llm_core.testing.scripted_chat_model import Answers
from llm_core.testing.scripted_chat_model import ScriptedChatConfig as BaseScriptedChatConfig
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


class ScriptedChatConfig(BaseScriptedChatConfig):
    """llm-core's scripted chat config with the game's answers.

    Each chain builds its own model, and each model gets its own pass through
    the script, so only the brain's action chain advances it.

    Attributes:
        script: The player's actions; empty for the world's judges.
    """

    script: list[Actions] = Field(default_factory=list)

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
