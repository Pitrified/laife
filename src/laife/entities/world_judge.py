"""World action judge - LLM-based validation for build and craft actions."""

from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from laife.data_models.basemodel_kwargs import BaseModelKwargs
from laife.llm_services.chat.config.base import ChatConfig


class WorldJudgeInput(BaseModelKwargs):
    """Input payload for WorldActionJudge.invoke / ainvoke.

    Field names define the required variables that every prompt template must
    contain; the validation in WorldActionJudge.__post_init__ derives the required
    set directly from these fields so the two can never drift apart.
    """

    action_type: str
    action_details: str
    observation: str
    player_state: str


class WorldJudgeResult(BaseModel):
    """Result from the world judge LLM."""

    success: bool
    feedback: str


_REQUIRED_PROMPT_VARS: frozenset[str] = frozenset(WorldJudgeInput.model_fields)


class MissingPromptVariablesError(ValueError):
    """Raised when a prompt template is missing required input variables."""

    def __init__(self, missing: set[str] | frozenset[str]) -> None:
        """Initialise with the set of missing variable names."""
        super().__init__(f"Prompt template is missing required variables: {sorted(missing)}")


@dataclass
class WorldActionJudge:
    """Judge whether a world action is valid using an LLM."""

    chat_config: ChatConfig
    prompt_str: str

    def __post_init__(self) -> None:
        """Validate the prompt template and build the LangChain chain."""
        self.prompt_template = ChatPromptTemplate.from_messages(
            [("system", self.prompt_str)],
            template_format="jinja2",
        )
        missing = _REQUIRED_PROMPT_VARS - set(self.prompt_template.input_variables)
        if missing:
            raise MissingPromptVariablesError(missing)
        self.model = self.chat_config.create_chat_model()
        self.structured_llm = self.model.with_structured_output(WorldJudgeResult)
        self.chain = self.prompt_template | self.structured_llm

    def invoke(self, judge_input: WorldJudgeInput) -> WorldJudgeResult:
        """Judge an action synchronously."""
        output = self.chain.invoke(judge_input.to_kw())
        if not isinstance(output, WorldJudgeResult):
            msg = f"Unexpected output type: {type(output)}"
            raise TypeError(msg)
        return output

    async def ainvoke(self, judge_input: WorldJudgeInput) -> WorldJudgeResult:
        """Judge an action asynchronously."""
        output = await self.chain.ainvoke(judge_input.to_kw())
        if not isinstance(output, WorldJudgeResult):
            msg = f"Unexpected output type: {type(output)}"
            raise TypeError(msg)
        return output
