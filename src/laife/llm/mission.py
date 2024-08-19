"""Mission for the player to complete."""

from enum import Enum


class MissionStatus(Enum):
    """Status of the mission."""

    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    COMPLETED = "completed"


class Mission:
    """Mission for the player to complete."""

    def __init__(
        self,
        objective: str,
        sub_level: int = 0,
    ) -> None:
        """Initialize the mission."""
        self.objective = objective
        self.history: list[str] = []
        self.status = MissionStatus.PENDING
        self.sub_missions: list[Mission] = []
        self.sub_level = sub_level
