"""Input and output of the reply chain, which answers a message from another player."""

from llm_core.data_models.basemodel_kwargs import BaseModelKwargs
from pydantic import BaseModel


class PlayerReplyInput(BaseModelKwargs):
    """Input of the reply chain; the field names are the prompt variables."""

    sender_name: str
    sender_prompt: str
    message: str
    own_state: str
    own_mission: str
    own_history: str


class PlayerReplyOutput(BaseModel):
    """Structured output returned by the replier LLM."""

    reply: str
