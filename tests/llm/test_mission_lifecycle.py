"""Unit tests for Mission lifecycle transitions (completion and failure)."""

import pytest

# NOTE: laife.entities.action must be imported before laife.llm.mission to
# avoid a circular import: mission.py imports BaseAction at module level for
# pydantic, which triggers laife.entities.__init__, which imports Player,
# which tries to import Mission from the not-yet-initialised mission module.
# Importing any entities submodule first breaks the cycle.
from laife.entities.action import BaseAction  # noqa: F401
from laife.llm.mission import MAX_MISSION_FAILURES
from laife.llm.mission import Mission
from laife.llm.mission import MissionStatus

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def active_mission() -> Mission:
    """Return a fresh ACTIVE mission."""
    return Mission(objective="Build a house", status=MissionStatus.ACTIVE)


# ---------------------------------------------------------------------------
# record_action_success
# ---------------------------------------------------------------------------


def test_record_action_success_marks_completed(active_mission: Mission) -> None:
    """Success call sets status to COMPLETED."""
    active_mission.record_action_success()
    assert active_mission.status == MissionStatus.COMPLETED


def test_record_action_success_resets_consecutive_failures(active_mission: Mission) -> None:
    """Success call resets the consecutive failure counter to zero."""
    active_mission.consecutive_failures = 3
    active_mission.record_action_success()
    assert active_mission.consecutive_failures == 0


# ---------------------------------------------------------------------------
# record_action_failure
# ---------------------------------------------------------------------------


def test_record_action_failure_increments_counter(active_mission: Mission) -> None:
    """Each failure call increments consecutive_failures by one."""
    active_mission.record_action_failure()
    assert active_mission.consecutive_failures == 1


def test_fewer_than_max_failures_stays_active(active_mission: Mission) -> None:
    """Fewer than max_failures consecutive failures leave the mission ACTIVE."""
    for _ in range(active_mission.max_failures - 1):
        active_mission.record_action_failure()
    assert active_mission.status == MissionStatus.ACTIVE


def test_max_failures_marks_failed(active_mission: Mission) -> None:
    """Exactly max_failures consecutive failures mark the mission FAILED."""
    for _ in range(active_mission.max_failures):
        active_mission.record_action_failure()
    assert active_mission.status == MissionStatus.FAILED


def test_default_max_failures_is_constant(active_mission: Mission) -> None:
    """max_failures defaults to the module-level MAX_MISSION_FAILURES constant."""
    assert active_mission.max_failures == MAX_MISSION_FAILURES


def test_custom_max_failures() -> None:
    """A custom max_failures value is respected."""
    m = Mission(objective="Test", status=MissionStatus.ACTIVE, max_failures=2)
    m.record_action_failure()
    assert m.status == MissionStatus.ACTIVE
    m.record_action_failure()
    assert m.status == MissionStatus.FAILED


# ---------------------------------------------------------------------------
# is_terminal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (MissionStatus.PENDING, False),
        (MissionStatus.ACTIVE, False),
        (MissionStatus.COMPLETED, True),
        (MissionStatus.FAILED, True),
    ],
)
def test_is_terminal(status: MissionStatus, expected: bool) -> None:  # noqa: FBT001
    """is_terminal returns True only for COMPLETED and FAILED."""
    m = Mission(objective="x", status=status)
    assert m.is_terminal() is expected
