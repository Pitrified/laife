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

    act: Actions = Field(..., description="The action to take.")
    reason: str = Field(..., description="The reason for the action.")

    def get_action_move(self) -> ActionMove:
        """Get the ActionMove."""
        if not isinstance(self.act, ActionMove):
            raise ValueError("Action is not an ActionMove")
        return self.act

    def get_action_build(self) -> ActionBuild:
        """Get the ActionBuild."""
        if not isinstance(self.act, ActionBuild):
            raise ValueError("Action is not an ActionBuild")
        return self.act

    def get_action_craft(self) -> ActionCraft:
        """Get the ActionCraft."""
        if not isinstance(self.act, ActionCraft):
            raise ValueError("Action is not an ActionCraft")
        return self.act
