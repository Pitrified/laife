"""Actions are something the Brain decides to do to solve a Mission."""

from dataclasses import dataclass

from pydantic import BaseModel
from pydantic import Field

from laife.data_models.basemodel_kwargs import BaseModelKwargs
from laife.entities.utils.directions import CardinalDirection
from laife.llm.structured_chain import StructuredLLMChain
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


class ActionPickerInput(BaseModelKwargs):
    """Input payload for ActionPicker.invoke / ainvoke.

    Field names define the required variables that every prompt template must
    contain; the validation in StructuredLLMChain.__post_init__ derives the
    required set directly from these fields so the two can never drift apart.
    """

    mission: str
    history: str
    observation: str
    player_state: str


@dataclass
class ActionPicker:
    """Pick an action to take."""

    chat_config: ChatConfig
    prompt_str: str

    def __post_init__(self) -> None:
        """Build the underlying structured chain."""
        self._chain: StructuredLLMChain[ActionPickerInput, ActionEnvelope] = StructuredLLMChain(
            chat_config=self.chat_config,
            prompt_str=self.prompt_str,
            input_model=ActionPickerInput,
            output_model=ActionEnvelope,
        )

    def invoke(self, action_input: ActionPickerInput) -> BaseAction:
        """Pick an action synchronously."""
        return self._chain.invoke(action_input).act

    async def ainvoke(self, action_input: ActionPickerInput) -> BaseAction:
        """Pick an action asynchronously."""
        return (await self._chain.ainvoke(action_input)).act
