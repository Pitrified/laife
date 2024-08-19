"""Channels to and from the World."""

import asyncio


class WorldResponse:
    """A response from the world."""

    def __init__(
        self,
        status: str,
        response_data: dict,
    ) -> None:
        """Initialize the response."""
        self.status = status
        self.response_data = response_data

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return (
            f"WorldResponse(status={self.status}, response_data={self.response_data})"
        )


class WorldRequest:
    """A request to the world."""

    def __init__(
        self,
        response_queue: asyncio.Queue[WorldResponse],
        request_type: str,
        request_data: dict,
    ) -> None:
        """Initialize the request."""
        self.response_queue = response_queue
        self.request_type = request_type
        self.request_data = request_data

    def __str__(self) -> str:
        """Return the string representation of the request."""
        return f"WorldRequest(request_type={self.request_type}, request_data={self.request_data})"
