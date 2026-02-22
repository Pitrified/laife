"""Chat config classes for each LLM provider."""

from laife.llm_services.chat.config.azure_openai import AzureOpenAIChatConfig
from laife.llm_services.chat.config.base import ChatConfig
from laife.llm_services.chat.config.chat_openai import ChatOpenAIConfig
from laife.llm_services.chat.config.huggingface import HuggingFaceChatConfig
from laife.llm_services.chat.config.ollama import OllamaChatConfig

__all__ = [
    "AzureOpenAIChatConfig",
    "ChatConfig",
    "ChatOpenAIConfig",
    "HuggingFaceChatConfig",
    "OllamaChatConfig",
]
