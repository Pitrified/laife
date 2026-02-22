"""HuggingFace chat configuration."""

from langchain_core.utils.utils import secret_from_env
from pydantic import Field
from pydantic import SecretStr

from laife.llm_services.chat.config.base import ChatConfig


class HuggingFaceChatConfig(ChatConfig):
    """Configuration for the HuggingFace chat model (via the Inference API)."""

    model: str = "HuggingFaceTB/SmolLM2-135M-Instruct"
    """HuggingFace model ID to use."""
    model_provider: str = "huggingface"
    """Provider name for init_chat_model."""
    api_key: SecretStr | None = Field(
        default_factory=secret_from_env("HUGGINGFACEHUB_API_TOKEN", default=None)
    )
    """HuggingFace API token. Reads HUGGINGFACEHUB_API_TOKEN env var by default."""
    max_tokens: int = 1024
    """Maximum number of tokens to generate."""
