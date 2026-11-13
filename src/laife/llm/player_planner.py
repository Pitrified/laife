"""Input and output of the planner chain, which splits a mission into ordered sub-missions."""

from llm_core.data_models.basemodel_kwargs import BaseModelKwargs
from pydantic import BaseModel
from pydantic import Field


class PlayerPlannerInput(BaseModelKwargs):
    """Input of the planner chain; the field names are the prompt variables."""

    mission: str
    history: str
    observation: str
    player_state: str


class PlayerPlannerResult(BaseModel):
    """Structured output returned by the planner LLM."""

    sub_missions: list[str] = Field(
        ...,
        description="Ordered list of sub-mission objectives to complete the top-level mission.",
        min_length=1,
    )
    reason: str = Field(..., description="Why these sub-missions were chosen.")
