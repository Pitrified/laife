"""Actions are something the Brain decides to do to solve a Mission."""

from pydantic import BaseModel, Field

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
    """Craft something."""

    item: str = Field(..., description="The item to craft.")
    description: str = Field(..., description="The description of the item.")


Actions = ActionMove | ActionBuild | ActionCraft


class Action(BaseModel):
    """An action to take."""

    action: Actions = Field(..., description="The action to take.")
    reason: str = Field(..., description="The reason for the action.")
