"""Actions are something the Brain decides to do to solve a Mission."""

from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import SystemMessagePromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from pydantic import Field

from laife.llm_services.chat.config.chat_openai import ChatOpenAIConfig
from laife.ui.directions import CardinalDirection


class ActionMove(BaseModel):
    """Move towards a direction."""

    direction: CardinalDirection = Field(..., description="The direction to move.")
    distance: int = Field(..., description="The distance to move.")


class ActionBuild(BaseModel):
    """Build something."""

    building_type: str = Field(..., description="The building to build.")
    description: str = Field(..., description="The description of the building.")
    size: int = Field(..., description="The size of the building.")


class ActionCraft(BaseModel):
    """Craft something, like an item or utensil.

    An item is a physical object that can be used to solve a mission.
    An utensil is a device that can be used to craft other items or utensils.
    """

    utensil_name: str = Field(..., description="The item or utensil to craft.")
    description: str = Field(..., description="The description of the item or utensil.")


Actions = ActionMove | ActionBuild | ActionCraft


class Action(BaseModel):
    """An action to take.

    The action does not necessarily have to solve the mission.
    A good action is one that helps solve the mission, possibly by taking
    other actions later.
    """

    act: Actions = Field(..., description="The action to take.")
    reason: str = Field(..., description="The reason for the action.")

    def get_action_move(self) -> ActionMove:
        """Get the ActionMove."""
        if not isinstance(self.act, ActionMove):
            msg = "Action is not an ActionMove"
            raise TypeError(msg)
        return self.act

    def get_action_build(self) -> ActionBuild:
        """Get the ActionBuild."""
        if not isinstance(self.act, ActionBuild):
            msg = "Action is not an ActionBuild"
            raise TypeError(msg)
        return self.act

    def get_action_craft(self) -> ActionCraft:
        """Get the ActionCraft."""
        if not isinstance(self.act, ActionCraft):
            msg = "Action is not an ActionCraft"
            raise TypeError(msg)
        return self.act


action_template = """You are an agent in a virtual world. \
You have a mission to complete. \
You can take an action to solve the mission. \

The mission is to: {mission}
"""
action_prompt = ChatPromptTemplate([SystemMessagePromptTemplate.from_template(action_template)])


@dataclass
class ActionPicker:
    """Pick an action to take."""

    chat_openai_config: ChatOpenAIConfig

    def __post_init__(self) -> None:
        """Initialize the action picker."""
        self.model = ChatOpenAI(**self.chat_openai_config.model_dump())
        self.structured_llm = self.model.with_structured_output(Action)
        self.chain = action_prompt | self.structured_llm

    def invoke(self, mission: str) -> Action:
        """Pick an action to take."""
        # MAYBE the mission is of type Mission
        output = self.chain.invoke({"mission": mission})
        if not isinstance(output, Action):
            msg = f"Unexpected output type: {type(output)}"
            raise TypeError(msg)
        return output
