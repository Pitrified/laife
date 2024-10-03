"""Mission for the player to complete."""

from enum import Enum
from typing import Self

from pydantic import BaseModel, Field


class MissionHistoryEntry(BaseModel):
    """History entry of a mission."""

    action: str
    result: str

    def to_prompt(self) -> str:
        """Return the history entry as a prompt."""
        return f"You tried to {self.action} and the result was {self.result}"


class MissionHistory(BaseModel):
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


class MissionType(Enum):
    """Type of the mission."""

    CRAFT = "craft"
    BUILD = "build"
    MOVE = "move"
    THINK = "think"


class MissionStep(BaseModel):
    """Mission for the player to complete."""

    mission_type: MissionType
    objective: str
    status: MissionStatus = MissionStatus.PENDING

    def to_prompt(self) -> str:
        """Return the mission as a prompt."""
        p = f"The mission is '{self.objective}'"
        p += f"\nStatus: {self.status.value}"
        return p


class Mission(BaseModel):
    steps: list[MissionStep] = Field(default_factory=list)

    @classmethod
    def from_step(cls, mission_step: MissionStep) -> Self:
        """Create a mission from a step."""
        return cls(steps=[mission_step])

    @classmethod
    def from_steps(cls, *mission_steps: MissionStep) -> Self:
        """Create a mission from steps."""
        return cls(steps=list(mission_steps))

    def add_step(self, mission_step: MissionStep) -> None:
        """Add a step to the mission."""
        self.steps.append(mission_step)

    def to_prompt(self) -> str:
        """Return the mission as a prompt."""
        p = ""
        for step in self.steps:
            p += step.to_prompt() + "\n"
        return p
