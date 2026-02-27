"""Generic LangChain structured-output chain with prompt-variable validation."""

from dataclasses import dataclass
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from laife.data_models.basemodel_kwargs import BaseModelKwargs
from laife.llm_services.chat.config.base import ChatConfig


class MissingPromptVariablesError(ValueError):
    """Raised when a prompt template is missing required input variables."""

    def __init__(self, missing: set[str] | frozenset[str]) -> None:
        """Initialise with the set of missing variable names."""
        super().__init__(f"Prompt template is missing required variables: {sorted(missing)}")


@dataclass
class StructuredLLMChain[InputT: BaseModelKwargs, OutputT: BaseModel]:
    """Reusable LangChain chain with a Jinja2 prompt and structured output.

    Pass the *input_model* class to drive the required-variable guard and the
    *output_model* class to configure ``with_structured_output``.  Both
    ``invoke`` and ``ainvoke`` return the validated ``OutputT`` instance
    directly.
    """

    chat_config: ChatConfig
    prompt_str: str
    input_model: type[InputT]
    output_model: type[OutputT]

    def __post_init__(self) -> None:
        """Validate the prompt template and build the LangChain chain."""
        self.prompt_template = ChatPromptTemplate.from_messages(
            [("system", self.prompt_str)],
            template_format="jinja2",
        )
        required = frozenset(self.input_model.model_fields)
        missing = required - set(self.prompt_template.input_variables)
        if missing:
            raise MissingPromptVariablesError(missing)
        model = self.chat_config.create_chat_model()
        structured_llm = model.with_structured_output(self.output_model)
        self.chain = self.prompt_template | structured_llm

    def invoke(self, chain_input: InputT) -> OutputT:
        """Run the chain synchronously and return the structured output."""
        output = self.chain.invoke(chain_input.to_kw())
        if not isinstance(output, self.output_model):
            msg = f"Unexpected output type: {type(output)}"
            raise TypeError(msg)
        return output  # type: ignore[return-value]

    async def ainvoke(self, chain_input: InputT) -> OutputT:
        """Run the chain asynchronously and return the structured output."""
        output = await self.chain.ainvoke(chain_input.to_kw())
        if not isinstance(output, self.output_model):
            msg = f"Unexpected output type: {type(output)}"
            raise TypeError(msg)
        return output  # type: ignore[return-value]

    # Expose chain internals for tests that need to patch the chain directly.
    def _get_chain(self) -> Any:  # noqa: ANN401
        """Return the internal LangChain chain (for testing only)."""
        return self.chain
