"""Actions are something the Brain decides to do to solve a Mission."""

from llm_core.data_models.basemodel_kwargs import BaseModelKwargs
from pydantic import BaseModel
from pydantic import Field

from laife.entities.utils.directions import CardinalDirection


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


class ActionComplete(BaseAction):
    """Signal that the current focus mission has been achieved."""

    outcome: str = Field(..., description="One-sentence description of what was accomplished.")


class ActionInteract(BaseAction):
    """Send a natural-language message to a nearby player.

    Only players can be addressed - buildings and terrain cannot receive
    messages, and the world rejects any non-player target.
    """

    target_name: str = Field(
        ...,
        description=(
            "Name of the player to address. Must be a player listed as a"
            " valid interaction target - buildings and terrain cannot be"
            " addressed."
        ),
    )
    message: str = Field(..., description="The message to send.")


Actions = ActionMove | ActionBuild | ActionCraft | ActionPlan | ActionComplete | ActionInteract


class ActionEnvelope(BaseModel):
    """An action to take, wrapped in LLM-friendly format."""

    act: Actions = Field(..., description="The action to take.")


class ActionPickerInput(BaseModelKwargs):
    """Input of the action chain; the field names are the prompt variables."""

    mission: str
    history: str
    observation: str
    player_state: str
    inventory: str
    nearby_players: str
