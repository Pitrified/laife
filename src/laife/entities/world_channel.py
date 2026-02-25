"""Channels to and from the World."""

import asyncio
from enum import StrEnum

from laife.entities.building import Building


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
