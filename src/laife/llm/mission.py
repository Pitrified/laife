"""Mission for the player to complete."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel
from pydantic import Field

from laife.entities.action import Action  # noqa: TC001

# TC001 is needed to let pydantic know what an Action is


class MissionHistoryEntry(BaseModel):
    """History entry of a mission."""

    action: Action
    result: str

    def to_prompt(self) -> str:
        """Return the history entry as a prompt."""
        return f"You tried to {self.action} and the result was {self.result}"


class MissionHistory(BaseModel):
    """Collection of mission history entries."""

    history: list[MissionHistoryEntry] = Field(default_factory=list)

    def add_history_entry(
        self,
        mission_history_entry: MissionHistoryEntry,
    ) -> None:
        """Add a history entry to the mission."""
        self.history.append(mission_history_entry)

    def to_prompt(self) -> str:
        """Return the history as a prompt."""
        p = ""
        for entry in self.history:
            p += entry.to_prompt() + "\n"
        return p


class MissionStatus(Enum):
    """Status of the mission."""

    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    COMPLETED = "completed"


class Mission(BaseModel):
    """A mission composed of ordered mission steps."""

    objective: str
    sub_mission_level: int = 0
    status: MissionStatus = MissionStatus.PENDING
    steps: list[Mission] = Field(default_factory=list)
    parent_mission: Mission | None = None

    def add_sub_mission(self, objective: str) -> None:
        """Add a sub-mission to the mission."""
        sm = Mission(
            objective=objective,
            sub_mission_level=self.sub_mission_level + 1,
            parent_mission=self,
        )
        self.steps.append(sm)

    def to_prompt(self) -> str:
        """Return the mission as a prompt."""
        # current mission objective
        p = f"[M{self.sub_mission_level}] The mission is '{self.objective}' ({self.status.value})"
        # context of what we plan to do later/have done before
        for step in self.steps:
            p += step.to_prompt() + "\n"
        # context of parent mission to ground to bigger picture
        pm = self.parent_mission
        while pm is not None:
            p += f"Parent mission [M{pm.sub_mission_level}]: {pm.objective} ({pm.status.value})\n"
            pm = pm.parent_mission
        return p
