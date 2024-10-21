"""Chat OpenAI configuration.

These are the default configuration settings for the OpenAI chat model.
"""

from langchain_core.utils.utils import secret_from_env
from pydantic import BaseModel, Field, SecretStr


class ChatOpenAIConfig(BaseModel):
    model: str = Field(default="gpt-4o-mini")
    """Model name to use."""
    temperature: float = 0.2
    """What sampling temperature to use."""
    api_key: SecretStr | None = Field(
        default_factory=secret_from_env("OPENAI_API_KEY", default=None)
    )


# from typing import Any, Dict, List, Mapping, Optional, Tuple, Union
# from langchain_core.utils.utils import from_env, secret_from_env
# from pydantic import BaseModel, ConfigDict, Field, SecretStr
# class ChatOpenAIConfig(BaseModel):
#     client: Any = Field(default=None, exclude=True)  #: :meta private:
#     async_client: Any = Field(default=None, exclude=True)  #: :meta private:
#     root_client: Any = Field(default=None, exclude=True)  #: :meta private:
#     root_async_client: Any = Field(default=None, exclude=True)  #: :meta private:
#     model_name: str = Field(default="gpt-3.5-turbo", alias="model")
#     """Model name to use."""
#     temperature: float = 0.7
#     """What sampling temperature to use."""
#     model_kwargs: Dict[str, Any] = Field(default_factory=dict)
#     """Holds any model parameters valid for `create` call not explicitly specified."""
#     openai_api_key: Optional[SecretStr] = Field(
#         alias="api_key", default_factory=secret_from_env("OPENAI_API_KEY", default=None)
#     )
#     openai_api_base: Optional[str] = Field(default=None, alias="base_url")
#     """Base URL path for API requests, leave blank if not using a proxy or service
#         emulator."""
#     openai_organization: Optional[str] = Field(default=None, alias="organization")
#     """Automatically inferred from env var `OPENAI_ORG_ID` if not provided."""
#     # to support explicit proxy for OpenAI
#     openai_proxy: Optional[str] = Field(
#         default_factory=from_env("OPENAI_PROXY", default=None)
#     )
#     request_timeout: Union[float, Tuple[float, float], Any, None] = Field(
#         default=None, alias="timeout"
#     )
#     """Timeout for requests to OpenAI completion API. Can be float, httpx.Timeout or
#         None."""
#     max_retries: int = 2
#     """Maximum number of retries to make when generating."""
#     presence_penalty: Optional[float] = None
#     """Penalizes repeated tokens."""
#     frequency_penalty: Optional[float] = None
#     """Penalizes repeated tokens according to frequency."""
#     seed: Optional[int] = None
#     """Seed for generation"""
#     logprobs: Optional[bool] = None
#     """Whether to return logprobs."""
#     top_logprobs: Optional[int] = None
#     """Number of most likely tokens to return at each token position, each with
#      an associated log probability. `logprobs` must be set to true
#      if this parameter is used."""
#     logit_bias: Optional[Dict[int, int]] = None
#     """Modify the likelihood of specified tokens appearing in the completion."""
#     streaming: bool = False
#     """Whether to stream the results or not."""
#     n: int = 1
#     """Number of chat completions to generate for each prompt."""
#     top_p: Optional[float] = None
#     """Total probability mass of tokens to consider at each step."""
#     max_tokens: Optional[int] = None
#     """Maximum number of tokens to generate."""
#     tiktoken_model_name: Optional[str] = None
#     """The model name to pass to tiktoken when using this class.
#     Tiktoken is used to count the number of tokens in documents to constrain
#     them to be under a certain limit. By default, when set to None, this will
#     be the same as the embedding model name. However, there are some cases
#     where you may want to use this Embedding class with a model name not
#     supported by tiktoken. This can include when using Azure embeddings or
#     when using one of the many model providers that expose an OpenAI-like
#     API but with different models. In those cases, in order to avoid erroring
#     when tiktoken is called, you can specify a model name to use here."""
#     default_headers: Union[Mapping[str, str], None] = None
#     default_query: Union[Mapping[str, object], None] = None
#     # Configure a custom httpx client. See the
#     # [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
#     http_client: Union[Any, None] = None
#     """Optional httpx.Client. Only used for sync invocations. Must specify
#         http_async_client as well if you'd like a custom client for async invocations.
#     """
#     http_async_client: Union[Any, None] = None
#     """Optional httpx.AsyncClient. Only used for async invocations. Must specify
#         http_client as well if you'd like a custom client for sync invocations."""
#     stop: Optional[Union[List[str], str]] = Field(default=None, alias="stop_sequences")
#     """Default stop sequences."""
#     extra_body: Optional[Mapping[str, Any]] = None
#     """Optional additional JSON properties to include in the request parameters when
#     making requests to OpenAI compatible APIs, such as vLLM."""
#     include_response_headers: bool = False
#     """Whether to include response headers in the output message response_metadata."""
#     disabled_params: Optional[Dict[str, Any]] = Field(default=None)
#     """Parameters of the OpenAI client or chat.completions endpoint that should be
#     disabled for the given model.
#     Should be specified as ``{"param": None | ['val1', 'val2']}`` where the key is the
#     parameter and the value is either None, meaning that parameter should never be
#     used, or it's a list of disabled values for the parameter.
#     For example, older models may not support the 'parallel_tool_calls' parameter at
#     all, in which case ``disabled_params={"parallel_tool_calls: None}`` can ben passed in.
#     If a parameter is disabled then it will not be used by default in any methods, e.g.
#     in :meth:`~langchain_openai.chat_models.base.ChatOpenAI.with_structured_output`.
#     However this does not prevent a user from directly passed in the parameter during
#     invocation.
#     """
#     model_config = ConfigDict(populate_by_name=True)
