"""Params for search services."""

from laife.params.env_type import EnvType


class SearchParams:
    """Params for search services."""

    def __init__(
        self,
        env_type: EnvType,
    ) -> None:
        """Load the params for search services."""
        self.env_type = env_type
        self.load_params()

    def load_params(self) -> None:
        """Load the params for search services."""
        self.load_common_params_pre()

    def load_common_params_pre(self) -> None:
        """Load the common params."""

    def __str__(self) -> str:
        """Provide String representation of the SearchParams."""
        s = "SearchParams:"
        return s

    def __repr__(self) -> str:
        """Provide String representation of the SearchParams."""
        return str(self)
