"""Channels to and from the World."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel

from laife.entities.world_map_observation import WorldMapObservation

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


class WResComplete(WRes):
    """Response from the world judge for a completion verification request."""

    feedback: str
    message: str = ""
    outcome: str = ""

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"WResComplete(status={self.status}, feedback={self.feedback!r})"


class WResInteract(WRes):
    """Response carrying the target player's LLM-generated reply."""

    target_prompt: str
    reply: str

    def __str__(self) -> str:
        """Return the string representation of the response."""
        return f"WResInteract(status={self.status}, reply={self.reply!r})"


@dataclass(kw_only=True, eq=False)
class WReq:
    """A request to the world.

    Compared by identity: a request is a one-off message owed its own reply
    on ``response_queue``, so two with the same fields are still two requests.
    """

    response_queue: asyncio.Queue[WRes]
    # Correlation metadata stamped by Player._world_request before the
    # request is enqueued; lets the struct log tie a request back to the
    # player turn that issued it.  Named player_name (not player) because
    # WRecMove already has a `player` attribute holding the actual Player
    # instance it's moving.
    player_name: str = field(default="", init=False)
    turn: int = field(default=-1, init=False)


@dataclass(kw_only=True, eq=False)
class WRecBuild(WReq):
    """A building request."""

    building: Building
    observation: str
    player_state: str


@dataclass(kw_only=True, eq=False)
class WRecCraft(WReq):
    """A craft request."""

    utensil_name: str
    description: str
    observation: str
    player_state: str


@dataclass(kw_only=True, eq=False)
class WRecObserve(WReq):
    """A request for a world-state observation centred on *position*."""

    position: Position


@dataclass(kw_only=True, eq=False)
class WRecMove(WReq):
    """Request to validate and confirm a one-step player move."""

    player: Player
    new_position: Position

    def __str__(self) -> str:
        """Name the player rather than printing the whole Player object."""
        return f"WRecMove(player={self.player.name}, new_position={self.new_position})"


@dataclass(kw_only=True, eq=False)
class WRecComplete(WReq):
    """Request the world to verify that a focus mission is done."""

    objective: str
    outcome: str
    observation: str
    player_state: str


@dataclass(kw_only=True, eq=False)
class WRecInteract(WReq):
    """Request to route a natural-language message from one player to another."""

    sender_name: str
    sender_prompt: str
    target_name: str
    message: str

    def __str__(self) -> str:
        """Leave out the long sender prompt."""
        return (
            f"WRecInteract(sender={self.sender_name!r}"
            f", target={self.target_name!r}"
            f", message={self.message!r})"
        )
