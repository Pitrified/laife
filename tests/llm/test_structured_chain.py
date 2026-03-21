"""Unit tests for StructuredLLMChain and MissingPromptVariablesError."""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from llm_core.chains.structured_chain import MissingPromptVariablesError
from llm_core.chains.structured_chain import StructuredLLMChain
from llm_core.chat.config.ollama import OllamaChatConfig
from pydantic import BaseModel
import pytest

from laife.data_models.basemodel_kwargs import BaseModelKwargs

# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


class _SampleInput(BaseModelKwargs):
    """Minimal input model for testing."""

    foo: str
    bar: str


class _SampleOutput(BaseModel):
    """Minimal output model for testing."""

    result: str


VALID_PROMPT = "Foo: {{ foo }}\nBar: {{ bar }}\n"
INCOMPLETE_PROMPT = "Foo: {{ foo }}\n"  # missing 'bar'


@pytest.fixture
def chat_config() -> OllamaChatConfig:
    """OllamaChatConfig for use in tests (no real LLM calls made)."""
    return OllamaChatConfig()


@pytest.fixture
def chain(chat_config: OllamaChatConfig) -> StructuredLLMChain[_SampleInput, _SampleOutput]:
    """StructuredLLMChain with __post_init__ patched to avoid LLM initialisation."""
    with patch(
        "llm_core.chains.structured_chain.StructuredLLMChain.__post_init__",
        lambda self: setattr(self, "_chain", MagicMock()),
    ):
        return StructuredLLMChain(
            chat_config=chat_config,
            prompt_str=VALID_PROMPT,
            input_model=_SampleInput,
            output_model=_SampleOutput,
        )


@pytest.fixture
def chain_input() -> _SampleInput:
    """Minimal valid input fixture."""
    return _SampleInput(foo="hello", bar="world")


# ---------------------------------------------------------------------------
# MissingPromptVariablesError
# ---------------------------------------------------------------------------


def test_missing_prompt_variables_error_lists_vars() -> None:
    """Error message must contain every missing variable name."""
    err = MissingPromptVariablesError({"alpha", "beta"})
    msg = str(err)
    assert "alpha" in msg
    assert "beta" in msg


def test_missing_prompt_variables_error_is_value_error() -> None:
    """MissingPromptVariablesError must be a subclass of ValueError."""
    assert issubclass(MissingPromptVariablesError, ValueError)


# ---------------------------------------------------------------------------
# StructuredLLMChain - construction
# ---------------------------------------------------------------------------


def test_chain_raises_on_missing_prompt_vars(chat_config: OllamaChatConfig) -> None:
    """StructuredLLMChain must raise MissingPromptVariablesError if prompt is incomplete."""
    with pytest.raises(MissingPromptVariablesError) as exc_info:
        StructuredLLMChain(
            chat_config=chat_config,
            prompt_str=INCOMPLETE_PROMPT,
            input_model=_SampleInput,
            output_model=_SampleOutput,
        )
    assert "bar" in str(exc_info.value)


def test_chain_accepts_complete_prompt(chat_config: OllamaChatConfig) -> None:
    """StructuredLLMChain must not raise when all required variables are present."""
    with patch("llm_core.chains.structured_chain.StructuredLLMChain.__post_init__", lambda _: None):
        c = StructuredLLMChain(
            chat_config=chat_config,
            prompt_str=VALID_PROMPT,
            input_model=_SampleInput,
            output_model=_SampleOutput,
        )
    assert c.prompt_str == VALID_PROMPT


# ---------------------------------------------------------------------------
# StructuredLLMChain - invoke
# ---------------------------------------------------------------------------


def test_invoke_returns_output(
    chain: StructuredLLMChain[_SampleInput, _SampleOutput],
    chain_input: _SampleInput,
) -> None:
    """invoke() must return the structured output from the underlying chain."""
    expected = _SampleOutput(result="ok")
    chain.chain.invoke = MagicMock(return_value=expected)

    result = chain.invoke(chain_input)

    assert result is expected
    chain.chain.invoke.assert_called_once_with(chain_input.to_kw())


def test_invoke_raises_on_wrong_type(
    chain: StructuredLLMChain[_SampleInput, _SampleOutput],
    chain_input: _SampleInput,
) -> None:
    """invoke() must raise TypeError when the chain returns an unexpected type."""
    chain.chain.invoke = MagicMock(return_value="not an output model")

    with pytest.raises(TypeError):
        chain.invoke(chain_input)


# ---------------------------------------------------------------------------
# StructuredLLMChain - ainvoke
# ---------------------------------------------------------------------------


def test_ainvoke_returns_output(
    chain: StructuredLLMChain[_SampleInput, _SampleOutput],
    chain_input: _SampleInput,
) -> None:
    """ainvoke() must return the structured output from the underlying chain."""
    expected = _SampleOutput(result="async ok")
    chain.chain.ainvoke = AsyncMock(return_value=expected)

    result = asyncio.run(chain.ainvoke(chain_input))

    assert result is expected
    chain.chain.ainvoke.assert_awaited_once_with(chain_input.to_kw())


def test_ainvoke_raises_on_wrong_type(
    chain: StructuredLLMChain[_SampleInput, _SampleOutput],
    chain_input: _SampleInput,
) -> None:
    """ainvoke() must raise TypeError when the chain returns an unexpected type."""
    chain.chain.ainvoke = AsyncMock(return_value=99)

    with pytest.raises(TypeError):
        asyncio.run(chain.ainvoke(chain_input))
