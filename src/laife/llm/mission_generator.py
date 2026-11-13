"""Input and output of the mission generator chain, which proposes a mission objective."""

from llm_core.data_models.basemodel_kwargs import BaseModelKwargs
from pydantic import BaseModel
from pydantic import Field


class MissionGeneratorInput(BaseModelKwargs):
    """Input of the mission generator chain; the field names are the prompt variables."""

    observation: str
    player_state: str
    inventory: str


class MissionGeneratorResult(BaseModel):
    """Structured output returned by the mission-generator LLM."""

    objective: str = Field(
        ...,
        description="A single, concrete mission objective for the player to pursue.",
    )
    reason: str = Field(
        ...,
        description="Brief explanation of why this objective fits the current situation.",
    )
