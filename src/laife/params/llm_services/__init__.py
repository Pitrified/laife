"""Holder for the LLM params to use in the project."""

from laife.params.env_type import EnvType
from laife.params.llm_services.chat import ChatParams
from laife.params.llm_services.search import SearchParams


class LLMServicesParams:
    """Params holder for LLM services."""

    def __init__(
        self,
        env_type: EnvType,
    ) -> None:
        """Load the params for LLM services."""
        self.env_type = env_type
        self.load_params()

    def load_params(self) -> None:
        """Load the params for LLM services."""
        self.load_common_params_pre()

    def load_common_params_pre(self) -> None:
        """Load the common params."""
        self.chat = ChatParams(self.env_type)
        self.vector_search = SearchParams(self.env_type)

    def __str__(self) -> str:
        """Provide String representation of the LLMServicesParams."""
        s = f"{self.chat}\n"
        s += f"{self.vector_search}\n"
        return s.rstrip()

    def __repr__(self) -> str:
        """Provide String representation of the LLMServicesParams."""
        return str(self)
