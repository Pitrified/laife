"""Channels to and from the World."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from laife.entities.world_map_observation import WorldMapObservation  # noqa: TC001

if TYPE_CHECKING:
    import asyncio

    from laife.config.types import Position
    from laife.entities.building import Building
    from laife.entities.player import Player


class WResStatus(StrEnum):
    """The status of a world response."""

    SUCCESS = "success"
    ERROR = "error"

    @classmethod
    def from_bool(cls, *, success: bool) -> WResStatus:
        """Return SUCCESS when *success* is True, ERROR otherwise."""
        return cls.SUCCESS if success else cls.ERROR


class WRes(BaseModel):
    """Base typed response from the world - carries only a status code.

    Callers should expect a concrete subclass (WResBuild, WResCraft,
    WResObserve, WResMoveStep, WResMove, WResPlan, or WResError) and cast
    or isinstance-check as appropriate.
    """

    status: WResStatus

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"{self.__class__.__name__}(status={self.status})"


class WResBuild(WRes):
    """Typed response for a build action (success or rejection)."""

    feedback: str

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"WResBuild(status={self.status}, feedback={self.feedback!r})"


class WResCraft(WRes):
    """Typed response for a craft action."""

    feedback: str

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"WResCraft(status={self.status}, feedback={self.feedback!r})"


class WResObserve(WRes):
    """Typed response for a world observation request."""

    observation: WorldMapObservation

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"WResObserve(status={self.status}, observation={self.observation})"


class WResMoveStep(WRes):
    """World's per-step move validation response (SUCCESS or collision ERROR)."""

    new_position: tuple[int, int] | None = None
    obstacle: str | None = None

    def __str__(self) -> str:
        """Return the string representation of the response."""
        if self.status == WResStatus.SUCCESS:
            return f"WResMoveStep(status={self.status}, new_position={self.new_position})"
        return f"WResMoveStep(status={self.status}, obstacle={self.obstacle!r})"


class WResMove(WRes):
    """Aggregated move response returned by Player.move() to the play loop."""

    message: str

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"WResMove(status={self.status}, message={self.message!r})"


class WResPlan(WRes):
    """Response from the player-local planner."""

    sub_missions: list[str]
    reason: str

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return (
            f"WResPlan(status={self.status}"
            f", sub_missions={self.sub_missions}"
            f", reason={self.reason!r})"
        )


class WResError(WRes):
    """Generic error response for unknown requests or internal failures."""

    message: str

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"WResError(status={self.status}, message={self.message!r})"


class WResInteract(WRes):
    """Response carrying the target player's LLM-generated reply."""

    target_prompt: str
    reply: str

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"WResInteract(status={self.status}, reply={self.reply!r})"


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
        observation: str,
        player_state: str,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Initialize the building request."""
        super().__init__(*args, **kwargs)
        self.building = building
        self.observation = observation
        self.player_state = player_state

    def __str__(self) -> str:
        """Return the string representation of the request."""
        return (
            f"WRecBuild(id={id(self)}"
            f", response_queue={self.response_queue}"
            f", building={self.building})"
        )


class WRecCraft(WReq):
    """A craft request."""

    def __init__(
        self,
        utensil_name: str,
        description: str,
        observation: str,
        player_state: str,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Initialize the craft request."""
        super().__init__(*args, **kwargs)
        self.utensil_name = utensil_name
        self.description = description
        self.observation = observation
        self.player_state = player_state

    def __str__(self) -> str:
        """Return the string representation of the request."""
        return (
            f"WRecCraft(id={id(self)}"
            f", utensil_name={self.utensil_name}"
            f", response_queue={self.response_queue})"
        )


class WRecObserve(WReq):
    """A request for a world-state observation centred on *position*."""

    def __init__(
        self,
        position: Position,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Initialize the observe request."""
        super().__init__(*args, **kwargs)
        self.position = position

    def __str__(self) -> str:
        """Return the string representation of the request."""
        return (
            f"WRecObserve(id={id(self)}"
            f", position={self.position}"
            f", response_queue={self.response_queue})"
        )


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


class WRecInteract(WReq):
    """Request to route a natural-language message from one player to another."""

    def __init__(
        self,
        sender_name: str,
        sender_prompt: str,
        target_name: str,
        message: str,
        *args,  # noqa: ANN002
        **kwargs,  # noqa: ANN003
    ) -> None:
        """Initialize the interact request."""
        super().__init__(*args, **kwargs)
        self.sender_name = sender_name
        self.sender_prompt = sender_prompt
        self.target_name = target_name
        self.message = message

    def __str__(self) -> str:
        """Return the string representation of the request."""
        return (
            f"WRecInteract(id={id(self)}"
            f", sender={self.sender_name!r}"
            f", target={self.target_name!r}"
            f", message={self.message!r})"
        )
