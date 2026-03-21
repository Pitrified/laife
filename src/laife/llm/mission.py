"""Mission for the player to complete."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel
from pydantic import Field

from laife.entities.action import BaseAction  # noqa: TC001

# TC001 is needed to let pydantic know what an Action is


class MissionHistoryEntry(BaseModel):
    """History entry of a mission."""

    action: BaseAction
    result: str

    def to_prompt(self) -> str:
        """Return the history entry as a prompt."""
        return f"You tried to <{self.action}> and the result was {self.result}\n"


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
            p += entry.to_prompt()
        return p


class MissionStatus(Enum):
    """Status of the mission."""

    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    COMPLETED = "completed"


MAX_MISSION_FAILURES: int = 5
"""Number of consecutive build/craft failures before a mission is marked FAILED."""


class Mission(BaseModel):
    """A mission composed of ordered mission steps."""

    objective: str
    sub_mission_level: int = 0
    status: MissionStatus = MissionStatus.PENDING
    steps: list[Mission] = Field(default_factory=list)
    parent_mission: Mission | None = None
    consecutive_failures: int = 0
    max_failures: int = MAX_MISSION_FAILURES

    def add_sub_mission(self, objective: str) -> None:
        """Add a sub-mission to the mission."""
        sm = Mission(
            objective=objective,
            sub_mission_level=self.sub_mission_level + 1,
            parent_mission=self,
        )
        self.steps.append(sm)

    def active_focus(self) -> Mission:
        """Return the deepest active sub-mission, or self if none."""
        for step in self.steps:
            if step.status == MissionStatus.ACTIVE:
                return step.active_focus()
        return self

    def advance(self) -> bool:
        """Activate the next pending step.

        Returns True if a new step was activated, False if all steps are done.
        When all steps are done, marks self as COMPLETED and propagates upward.
        """
        for step in self.steps:
            if step.status == MissionStatus.PENDING:
                step.status = MissionStatus.ACTIVE
                return True
        # All steps accounted for - mark self completed and ask parent to advance
        self.status = MissionStatus.COMPLETED
        if self.parent_mission is not None:
            self.parent_mission.advance()
        return False

    def record_action_success(self) -> None:
        """Record a successful build or craft action and mark the mission COMPLETED."""
        self.consecutive_failures = 0
        self.status = MissionStatus.COMPLETED

    def record_action_failure(self) -> None:
        """Record a failed build or craft action.

        Increments the consecutive failure counter.  When the counter reaches
        ``max_failures`` the mission is marked ``FAILED``.
        """
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_failures:
            self.status = MissionStatus.FAILED

    def is_terminal(self) -> bool:
        """Return True when the mission has reached a final state (COMPLETED or FAILED)."""
        return self.status in (MissionStatus.COMPLETED, MissionStatus.FAILED)

    def to_prompt(self, *, top_prompt: bool = True, focus: Mission | None = None) -> str:
        """Return the mission as a prompt.

        Steps that match *focus* are prefixed with ``[FOCUS]`` so the LLM
        knows exactly which sub-mission to work on.
        """
        # current mission objective
        p = f"[M{self.sub_mission_level}] The mission is '{self.objective}' ({self.status.value})\n"
        # context of what we plan to do later/have done before
        for step in self.steps:
            if focus is not None and step is focus:
                p += f"[FOCUS]{step.to_prompt(top_prompt=False, focus=focus)}"
            else:
                p += step.to_prompt(top_prompt=False, focus=focus)
        # context of parent mission to ground to bigger picture
        if top_prompt:
            pm = self.parent_mission
            while pm is not None:
                p += f"[PM{pm.sub_mission_level}]: {pm.objective} ({pm.status.value})\n"
                pm = pm.parent_mission
        return p
