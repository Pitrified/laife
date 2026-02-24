"""Actions are something the Brain decides to do to solve a Mission."""

from dataclasses import dataclass
from typing import TypeVar

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import SystemMessagePromptTemplate
from pydantic import BaseModel
from pydantic import Field

from laife.entities.utils.directions import CardinalDirection
from laife.llm_services.chat.config.base import ChatConfig

T = TypeVar("T", bound=BaseModel)


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


action_template = """You are an agent in a virtual world. \
You have a mission to complete. \
You can take an action to solve the mission. \

The mission is to: {mission}
"""
action_prompt = ChatPromptTemplate([SystemMessagePromptTemplate.from_template(action_template)])


@dataclass
class ActionPicker:
    """Pick an action to take."""

    chat_config: ChatConfig

    def __post_init__(self) -> None:
        """Initialize the action picker."""
        self.model = self.chat_config.create_chat_model()
        self.structured_llm = self.model.with_structured_output(ActionEnvelope)
        self.chain = action_prompt | self.structured_llm

    def invoke(self, mission: str) -> BaseAction:
        """Pick an action to take."""
        # MAYBE the mission is of type Mission
        output = self.chain.invoke({"mission": mission})
        if not isinstance(output, ActionEnvelope):
            msg = f"Unexpected output type: {type(output)}"
            raise TypeError(msg)
        return output.act
