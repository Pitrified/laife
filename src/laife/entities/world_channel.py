"""Channels to and from the World."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import asyncio

    from laife.config.types import Position
    from laife.entities.building import Building
    from laife.entities.player import Player


class WResStatus(StrEnum):
    """The status of a world response."""

    SUCCESS = "success"
    ERROR = "error"


class WRes:
    """A response from the world."""

    def __init__(
        self,
        status: WResStatus,
        response_data: dict,
    ) -> None:
        """Initialize the response."""
        self.status = status
        self.response_data = response_data

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"WRes(status={self.status}, response_data={self.response_data})"


class WReq:
    """A request to the world."""

    def __init__(
        self,
        response_queue: asyncio.Queue[WRes],
    ) -> None:
        """Initialize the request."""
        self.response_queue = response_queue

    def __str__(self) -> str:
        """Return the string representation of the request."""
        return f"WReq(id={id(self)}, response_queue={self.response_queue})"


class WRecBuild(WReq):
    """A building request."""

    def __init__(
        self,
        building: Building,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Initialize the building request."""
        super().__init__(*args, **kwargs)
        self.building = building

    def __str__(self) -> str:
        """Return the string representation of the request."""
        return (
            f"WRecBuild(id={id(self)}"
            f", response_queue={self.response_queue}"
            f", building={self.building})"
        )


class WRecObserve(WReq):
    """A request for a world-state description to be used as an observation."""

    def __init__(
        self,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Initialize the observe request."""
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        """Return the string representation of the request."""
        return f"WRecObserve(id={id(self)}, response_queue={self.response_queue})"


class WRecMove(WReq):
    """Request to validate and confirm a one-step player move."""

    def __init__(
        self,
        player: Player,
        new_position: Position,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Initialize the move request."""
        super().__init__(*args, **kwargs)
        self.player = player
        self.new_position = new_position

    def __str__(self) -> str:
        """Return the string representation of the request."""
        return (
            f"WRecMove(id={id(self)}, player={self.player.name}, new_position={self.new_position})"
        )
