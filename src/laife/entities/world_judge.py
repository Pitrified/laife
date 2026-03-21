"""World action judge - LLM-based validation for build and craft actions."""

from dataclasses import dataclass

from llm_core.chains.structured_chain import StructuredLLMChain
from llm_core.chat.config.base import ChatConfig
from pydantic import BaseModel

from laife.data_models.basemodel_kwargs import BaseModelKwargs


class WorldJudgeInput(BaseModelKwargs):
    """Input payload for WorldActionJudge.invoke / ainvoke.

    Field names define the required variables that every prompt template must
    contain; the validation in StructuredLLMChain.__post_init__ derives the
    required set directly from these fields so the two can never drift apart.
    """

    action_type: str
    action_details: str
    observation: str
    player_state: str


class WorldJudgeResult(BaseModel):
    """Result from the world judge LLM."""

    success: bool
    feedback: str


@dataclass
class WorldActionJudge:
    """Judge whether a world action is valid using an LLM."""

    chat_config: ChatConfig
    prompt_str: str

    def __post_init__(self) -> None:
        """Build the underlying structured chain."""
        self._chain: StructuredLLMChain[WorldJudgeInput, WorldJudgeResult] = StructuredLLMChain(
            chat_config=self.chat_config,
            prompt_str=self.prompt_str,
            input_model=WorldJudgeInput,
            output_model=WorldJudgeResult,
        )

    def invoke(self, judge_input: WorldJudgeInput) -> WorldJudgeResult:
        """Judge an action synchronously."""
        return self._chain.invoke(judge_input)

    async def ainvoke(self, judge_input: WorldJudgeInput) -> WorldJudgeResult:
        """Judge an action asynchronously."""
        return await self._chain.ainvoke(judge_input)
