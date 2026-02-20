"""Base class for LLM services chat configuration."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from laife.data_models.basemodel_kwargs import BaseModelKwargs


class ChatConfig(BaseModelKwargs):
    """Base config for a chat model, usable with langchain's init_chat_model."""

    model: str
    model_provider: str
    temperature: float = 0.2

    def create_chat_model(self) -> BaseChatModel:
        """Instantiate the chat model from the config."""
        return init_chat_model(**self.to_kw(exclude_none=True))
