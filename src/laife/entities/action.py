"""Actions are something the Brain decides to do to solve a Mission."""

from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from pydantic import Field

from laife.entities.utils.directions import CardinalDirection
from laife.llm_services.chat.config.base import ChatConfig


class BaseAction(BaseModel):
    """Base class for all agent actions.

    The action does not necessarily have to solve the mission.
    A good action is one that helps solve the mission, possibly by taking
    other actions later.
    """

    reason: str = Field(..., description="Why this action was chosen.")


class ActionMove(BaseAction):
    """Move towards a direction."""

    direction: CardinalDirection = Field(..., description="The direction to move.")
    distance: int = Field(..., description="The distance to move.")


class ActionBuild(BaseAction):
    """Build something."""

    building_type: str = Field(..., description="The building to build.")
    description: str = Field(..., description="The description of the building.")
    size: int = Field(..., description="The size of the building.")


class ActionCraft(BaseAction):
    """Craft something, like an item or utensil.

    An item is a physical object that can be used to solve a mission.
    An utensil is a device that can be used to craft other items or utensils.
    """

    utensil_name: str = Field(..., description="The item or utensil to craft.")
    description: str = Field(..., description="The description of the item or utensil.")


class ActionPlan(BaseAction):
    """Plan the next steps for the mission."""


Actions = ActionMove | ActionBuild | ActionCraft | ActionPlan


class ActionEnvelope(BaseModel):
    """An action to take, wrapped in LLM-friendly format."""

    act: Actions = Field(..., description="The action to take.")


_REQUIRED_PROMPT_VARS: frozenset[str] = frozenset(
    {"mission", "history", "observation", "player_state"}
)


class MissingPromptVariablesError(ValueError):
    """Raised when a prompt template is missing required input variables."""

    def __init__(self, missing: set[str] | frozenset[str]) -> None:
        """Initialise with the set of missing variable names."""
        super().__init__(f"Prompt template is missing required variables: {sorted(missing)}")


@dataclass
class ActionPicker:
    """Pick an action to take."""

    chat_config: ChatConfig
    prompt_str: str

    def __post_init__(self) -> None:
        """Validate the prompt template and build the LangChain chain."""
        self.prompt_template = ChatPromptTemplate.from_messages(
            [("system", self.prompt_str)],
            template_format="jinja2",
        )
        missing = _REQUIRED_PROMPT_VARS - set(self.prompt_template.input_variables)
        if missing:
            raise MissingPromptVariablesError(missing)
        self.model = self.chat_config.create_chat_model()
        self.structured_llm = self.model.with_structured_output(ActionEnvelope)
        self.chain = self.prompt_template | self.structured_llm

    def invoke(
        self,
        mission: str,
        history: str,
        observation: str,
        player_state: str,
    ) -> BaseAction:
        """Pick an action synchronously."""
        output = self.chain.invoke(
            {
                "mission": mission,
                "history": history,
                "observation": observation,
                "player_state": player_state,
            }
        )
        if not isinstance(output, ActionEnvelope):
            msg = f"Unexpected output type: {type(output)}"
            raise TypeError(msg)
        return output.act

    async def ainvoke(
        self,
        mission: str,
        history: str,
        observation: str,
        player_state: str,
    ) -> BaseAction:
        """Pick an action asynchronously."""
        output = await self.chain.ainvoke(
            {
                "mission": mission,
                "history": history,
                "observation": observation,
                "player_state": player_state,
            }
        )
        if not isinstance(output, ActionEnvelope):
            msg = f"Unexpected output type: {type(output)}"
            raise TypeError(msg)
        return output.act
