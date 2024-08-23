"""Mission for the player to complete."""

from enum import Enum


class MissionHistoryEntry:
    """History entry of a mission."""

    def __init__(
        self,
        action: str,
        result: str,
    ) -> None:
        """Initialize the history entry."""
        self.action = action
        self.result = result

    def to_prompt(self) -> str:
        """Return the history entry as a prompt."""
        return f"You tried to {self.action} and the result was {self.result}"


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
        self.history: list[MissionHistoryEntry] = []
        self.status = MissionStatus.PENDING
        self.sub_missions: list[Mission] = []
        self.sub_level = sub_level

    def add_history_entry(
        self,
        action: str,
        result: str,
    ) -> None:
        """Add a history entry to the mission."""
        self.history.append(MissionHistoryEntry(action, result))

    def add_sub_mission(
        self,
        mission: "Mission",
    ) -> None:
        """Add a sub mission to the mission."""
        self.sub_missions.append(mission)

    def to_prompt(self) -> str:
        """Return the mission as a prompt."""
        p = f"The mission is '{self.objective}'"
        p += f"\nStatus: {self.status.value}"
        if self.sub_level > 0:
            p += f"\nSub mission level: {self.sub_level}"
        if len(self.history) > 0:
            p += f"\nFor now, the steps you took are:"
            for h in self.history:
                p += f"\n{h.to_prompt()}"
        if len(self.sub_missions) > 0:
            p += f"\nSub missions:"
            for sm in self.sub_missions:
                p += f"\n{sm.to_prompt()}"
        return p
