"""Params for chat services."""

from laife.params.env_type import EnvType


class ChatParams:
    """Params for chat services."""

    def __init__(
        self,
        env_type: EnvType,
    ) -> None:
        """Load the params for chat services."""
        self.env_type = env_type
        self.load_params()

    def load_params(self) -> None:
        """Load the params for chat services."""
        self.load_common_params_pre()

    def load_common_params_pre(self) -> None:
        """Load the common params."""

    def __str__(self) -> str:
        """Provide String representation of the ChatParams."""
        s = "ChatParams:"
        return s

    def __repr__(self) -> str:
        """Provide String representation of the ChatParams."""
        return str(self)
