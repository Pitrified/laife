"""Channels to and from the World."""

import asyncio
from enum import StrEnum

from laife.entities.building import Building


class WorldResponseStatus(StrEnum):
    """The status of a world response."""

    SUCCESS = "success"
    ERROR = "error"


class WorldResponse:
    """A response from the world."""

    def __init__(
        self,
        status: WorldResponseStatus,
        response_data: dict,
    ) -> None:
        """Initialize the response."""
        self.status = status
        self.response_data = response_data

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"WorldResponse(status={self.status}, response_data={self.response_data})"


class WorldRequest:
    """A request to the world."""

    def __init__(
        self,
        response_queue: asyncio.Queue[WorldResponse],
    ) -> None:
        """Initialize the request."""
        self.response_queue = response_queue

    def __str__(self) -> str:
        """Return the string representation of the request."""
        return f"WorldRequest(id={id(self)}, response_queue={self.response_queue})"


class WRBuild(WorldRequest):
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
            f"WRBuild(id={id(self)}"
            f", response_queue={self.response_queue}"
            f", building={self.building})"
        )
