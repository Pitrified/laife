"""A chat model that answers from a fixed script, for running the game with no provider.

Every chain in the game asks for structured output, so the model answers
``with_structured_output(schema)`` by schema: the player brain gets the next
action of its script, cycling, and every other chain gets a fixed value.

Each player builds its own chains, so each player gets its own
:class:`ScriptedChatConfig` carrying its own script; the world's judges get
one with an empty script, since they never ask for an action.
"""

from typing import TYPE_CHECKING
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.runnables import RunnableLambda
from llm_core.chat.config.base import ChatConfig
from pydantic import BaseModel
from pydantic import Field
from pydantic import PrivateAttr

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

if TYPE_CHECKING:
    from langchain_core.callbacks import CallbackManagerForLLMRun
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import ChatResult


class UnscriptedSchemaError(Exception):
    """A chain asked the scripted model for an output model it has no answer for."""

    def __init__(self, schema: object) -> None:
        """Name the schema, so a new chain shows up as this failure."""
        super().__init__(f"No scripted answer for output model {schema!r}")


class EmptyScriptError(Exception):
    """An action was asked of a scripted model whose script is empty."""

    def __init__(self) -> None:
        """Explain where the script comes from."""
        super().__init__(
            "The scripted model was asked for an action but its script is empty;"
            " give the player a ScriptedChatConfig with a script."
        )


class UnscriptedCallError(Exception):
    """The scripted model was called for free text; only structured output is scripted."""

    def __init__(self) -> None:
        """Explain which call is supported."""
        super().__init__("The scripted model only answers with_structured_output calls.")


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


class ScriptedChatModel(BaseChatModel):
    """Chat model that answers structured-output calls from a script. No API calls.

    Attributes:
        script: Actions handed out in order to the player brain, cycling.
    """

    script: list[Actions]

    _next_action: int = PrivateAttr(default=0)

    def _generate(
        self,
        messages: list[BaseMessage],  # noqa: ARG002
        stop: list[str] | None = None,  # noqa: ARG002
        run_manager: CallbackManagerForLLMRun | None = None,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002, ANN401
    ) -> ChatResult:
        raise UnscriptedCallError

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def with_structured_output(
        self,
        schema: type[BaseModel] | dict[str, Any],
        *,
        include_raw: bool = False,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002, ANN401
    ) -> Runnable:
        """Return a runnable that ignores the prompt and answers for *schema*."""
        return RunnableLambda(lambda _prompt: self.answer(schema))

    def answer(self, schema: object) -> BaseModel:
        """Return the scripted instance of *schema*."""
        if schema is ActionEnvelope:
            return ActionEnvelope(act=self._take_action())
        if schema is WorldJudgeResult:
            return WorldJudgeResult(success=True, feedback="scripted: approved")
        if schema is MissionGeneratorResult:
            return MissionGeneratorResult(
                objective="Build a shed and craft a hammer.",
                reason="scripted: fixed objective",
            )
        if schema is PlayerPlannerResult:
            return PlayerPlannerResult(
                sub_missions=["Build a shed.", "Craft a hammer."],
                reason="scripted: fixed plan",
            )
        if schema is PlayerReplyOutput:
            return PlayerReplyOutput(reply="scripted: going well, thanks.")
        raise UnscriptedSchemaError(schema)

    def _take_action(self) -> Actions:
        """Return a copy of the next action in the script, wrapping at the end."""
        if not self.script:
            raise EmptyScriptError
        action = self.script[self._next_action % len(self.script)]
        self._next_action += 1
        return action.model_copy()


class ScriptedChatConfig(ChatConfig):
    """Chat config that builds a :class:`ScriptedChatModel`.

    Each chain builds its own model from the config, so only the brain's
    model advances through the script.

    Attributes:
        script: The player's actions; empty for the world's judges.
        model: Recorded in the ``llm_call`` log events as ``scripted``.
        model_provider: Satisfies ``ChatConfig``; unused.
    """

    script: list[Actions] = Field(default_factory=list)
    model: str = "scripted"
    model_provider: str = "scripted"

    def create_chat_model(self) -> ScriptedChatModel:
        """Return a scripted model with this config's script."""
        return ScriptedChatModel(script=self.script)
