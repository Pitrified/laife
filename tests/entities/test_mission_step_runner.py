"""Tests for Mission.active_focus, Mission.advance, and Player step-runner integration."""

import asyncio
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from laife.entities.action import ActionComplete
from laife.entities.action import ActionPlan
from laife.entities.player import Player
from laife.entities.player import PlayerState
from laife.entities.world_channel import WRecComplete
from laife.entities.world_channel import WResComplete
from laife.entities.world_channel import WResStatus
from laife.entities.world_map_observation import WorldMapObservation
from laife.llm.mission import Mission
from laife.llm.mission import MissionHistory
from laife.llm.mission import MissionStatus
from laife.llm.player_planner import PlayerPlannerResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mission(objective: str, status: MissionStatus = MissionStatus.ACTIVE) -> Mission:
    """Create a standalone Mission (no parent)."""
    return Mission(objective=objective, status=status)


def _stubbed_player(objective: str = "Build a house") -> Player:
    """Minimal Player constructed without __init__ for unit testing."""
    player: Player = object.__new__(Player)
    player.name = "tester"
    player.position = (0, 0)
    player.state = PlayerState.IDLE
    player.mission = Mission(objective=objective, status=MissionStatus.ACTIVE)
    player.history = MissionHistory()
    player.last_observation = WorldMapObservation.from_position((0, 0))
    player.planner = MagicMock()
    player.brain = MagicMock()
    # Async world queue: put() is a no-op AsyncMock; input_queue is a real queue
    player.world_input_queue = MagicMock()
    player.world_input_queue.put = AsyncMock()
    player.input_queue = asyncio.Queue()
    return player


# ---------------------------------------------------------------------------
# Mission.active_focus
# ---------------------------------------------------------------------------


def test_active_focus_no_steps() -> None:
    """active_focus() on a leaf mission returns self."""
    m = _make_mission("Top level")
    assert m.active_focus() is m


def test_active_focus_first_active_step() -> None:
    """active_focus() returns the first ACTIVE sub-mission."""
    parent = _make_mission("Top")
    parent.add_sub_mission("Step A")
    parent.steps[0].status = MissionStatus.ACTIVE
    parent.add_sub_mission("Step B")

    result = parent.active_focus()
    assert result is parent.steps[0]
    assert result.objective == "Step A"


def test_active_focus_skips_pending_steps() -> None:
    """active_focus() skips PENDING sub-missions and returns self when none are ACTIVE."""
    parent = _make_mission("Top")
    parent.add_sub_mission("Step A")  # PENDING by default
    parent.add_sub_mission("Step B")

    # None are ACTIVE yet, so active_focus should return the parent itself
    assert parent.active_focus() is parent


def test_active_focus_nested() -> None:
    """active_focus() descends into nested sub-missions."""
    root = _make_mission("Root")
    root.add_sub_mission("Child")
    child = root.steps[0]
    child.status = MissionStatus.ACTIVE
    child.add_sub_mission("Grandchild")
    grandchild = child.steps[0]
    grandchild.status = MissionStatus.ACTIVE

    result = root.active_focus()
    assert result is grandchild
    assert result.objective == "Grandchild"


# ---------------------------------------------------------------------------
# Mission.advance
# ---------------------------------------------------------------------------


def test_advance_activates_next_pending() -> None:
    """advance() flips the first PENDING sub-mission to ACTIVE and returns True."""
    m = _make_mission("Top")
    m.add_sub_mission("Step A")
    m.add_sub_mission("Step B")

    advanced = m.advance()

    assert advanced is True
    assert m.steps[0].status == MissionStatus.ACTIVE
    assert m.steps[1].status == MissionStatus.PENDING


def test_advance_activates_next_after_first_completed() -> None:
    """advance() skips COMPLETED steps and activates the next PENDING one."""
    m = _make_mission("Top")
    m.add_sub_mission("Step A")
    m.add_sub_mission("Step B")
    m.steps[0].status = MissionStatus.COMPLETED

    advanced = m.advance()

    assert advanced is True
    assert m.steps[1].status == MissionStatus.ACTIVE


def test_advance_returns_false_when_all_done() -> None:
    """advance() marks self COMPLETED and returns False when no PENDING steps remain."""
    m = _make_mission("Top")
    m.add_sub_mission("Step A")
    m.steps[0].status = MissionStatus.COMPLETED

    advanced = m.advance()

    assert advanced is False
    assert m.status == MissionStatus.COMPLETED


def test_advance_propagates_to_parent() -> None:
    """advance() propagates completion upward and activates the next sibling."""
    root = _make_mission("Root")
    root.add_sub_mission("Child A")
    root.add_sub_mission("Child B")

    child_a = root.steps[0]
    child_a.status = MissionStatus.ACTIVE
    child_a.advance()  # child A has no sub-steps so it completes itself and tells root

    # root.advance() should have activated Child B
    assert child_a.status == MissionStatus.COMPLETED
    assert root.steps[1].status == MissionStatus.ACTIVE


# ---------------------------------------------------------------------------
# Mission.to_prompt with focus marker
# ---------------------------------------------------------------------------


def test_to_prompt_marks_focus() -> None:
    """to_prompt(focus=step) prefixes the focused step with [FOCUS]."""
    m = _make_mission("Top")
    m.add_sub_mission("Step A")
    m.steps[0].status = MissionStatus.ACTIVE
    m.add_sub_mission("Step B")

    focused_step = m.steps[0]
    prompt = m.to_prompt(focus=focused_step)

    assert "[FOCUS]" in prompt
    # The [FOCUS] marker should precede Step A's entry
    idx_focus = prompt.index("[FOCUS]")
    idx_step_a = prompt.index("Step A")
    assert idx_focus < idx_step_a


def test_to_prompt_no_focus_no_marker() -> None:
    """to_prompt() without focus argument never emits [FOCUS]."""
    m = _make_mission("Top")
    m.add_sub_mission("Step A")
    m.steps[0].status = MissionStatus.ACTIVE

    assert "[FOCUS]" not in m.to_prompt()


# ---------------------------------------------------------------------------
# Player.plan() activates the first sub-mission
# ---------------------------------------------------------------------------


def test_plan_activates_first_sub_mission() -> None:
    """After Player.plan(), the first appended sub-mission is ACTIVE."""
    player = _stubbed_player()
    result = PlayerPlannerResult(
        sub_missions=["Step A", "Step B"],
        reason="Breaking it down",
    )
    player.planner.ainvoke = AsyncMock(return_value=result)

    action = ActionPlan(reason="Need a plan")
    asyncio.run(player.plan(action))

    assert player.mission.steps[0].status == MissionStatus.ACTIVE
    assert player.mission.steps[1].status == MissionStatus.PENDING


def test_plan_resets_history() -> None:
    """Player.plan() resets the mission history."""
    from laife.llm.mission import MissionHistoryEntry  # noqa: PLC0415

    player = _stubbed_player()
    # Add a stale history entry
    entry = MissionHistoryEntry(action=ActionPlan(reason="old"), result="old result")
    player.history.add_history_entry(entry)

    result = PlayerPlannerResult(sub_missions=["Step A"], reason="reason")
    player.planner.ainvoke = AsyncMock(return_value=result)

    asyncio.run(player.plan(ActionPlan(reason="replan")))

    assert player.history.history == []


# ---------------------------------------------------------------------------
# Player.complete - handler tests
# ---------------------------------------------------------------------------


def test_complete_marks_focus_done_and_advances() -> None:
    """Player.complete() marks the active focus COMPLETED and activates the next step."""
    player = _stubbed_player()
    player.mission.add_sub_mission("Step A")
    player.mission.add_sub_mission("Step B")
    player.mission.steps[0].status = MissionStatus.ACTIVE
    player.input_queue.put_nowait(WResComplete(status=WResStatus.SUCCESS, feedback="world ok"))

    action = ActionComplete(reason="done", outcome="Finished step A")
    asyncio.run(player.complete(action))

    assert player.mission.steps[0].status == MissionStatus.COMPLETED
    assert player.mission.steps[1].status == MissionStatus.ACTIVE


def test_complete_resets_history() -> None:
    """Player.complete() clears the mission history for the new focus."""
    from laife.llm.mission import MissionHistoryEntry  # noqa: PLC0415

    player = _stubbed_player()
    player.mission.add_sub_mission("Step A")
    player.mission.steps[0].status = MissionStatus.ACTIVE
    entry = MissionHistoryEntry(
        action=ActionComplete(reason="r", outcome="o"), result="some result"
    )
    player.history.add_history_entry(entry)
    player.input_queue.put_nowait(WResComplete(status=WResStatus.SUCCESS, feedback="world ok"))

    asyncio.run(player.complete(ActionComplete(reason="done", outcome="ok")))

    assert player.history.history == []


def test_complete_returns_success() -> None:
    """Player.complete() returns WRes with SUCCESS status."""
    player = _stubbed_player()
    player.mission.add_sub_mission("Step A")
    player.mission.steps[0].status = MissionStatus.ACTIVE
    player.input_queue.put_nowait(WResComplete(status=WResStatus.SUCCESS, feedback="world ok"))

    action = ActionComplete(reason="done", outcome="Step A completed")
    wrsp = asyncio.run(player.complete(action))

    assert wrsp.status == WResStatus.SUCCESS
    assert wrsp.outcome == "Step A completed"


def test_complete_no_next_step_message() -> None:
    """When the last step is completed, the response message says 'all steps done'."""
    player = _stubbed_player()
    player.mission.add_sub_mission("Only step")
    player.mission.steps[0].status = MissionStatus.ACTIVE
    player.input_queue.put_nowait(WResComplete(status=WResStatus.SUCCESS, feedback="world ok"))

    wrsp = asyncio.run(player.complete(ActionComplete(reason="done", outcome="done")))

    assert "all steps done" in wrsp.message.lower()


# ---------------------------------------------------------------------------
# Player.complete - world round-trip tests
# ---------------------------------------------------------------------------


def test_complete_world_rejected() -> None:
    """When world returns ERROR the focus mission stays ACTIVE and WRes is ERROR."""
    player = _stubbed_player()
    player.mission.add_sub_mission("Step A")
    player.mission.steps[0].status = MissionStatus.ACTIVE
    player.input_queue.put_nowait(WResComplete(status=WResStatus.ERROR, feedback="not done yet"))

    wrsp = asyncio.run(player.complete(ActionComplete(reason="done", outcome="claimed done")))

    assert wrsp.status == WResStatus.ERROR
    assert player.mission.steps[0].status == MissionStatus.ACTIVE


def test_complete_world_approved_advances() -> None:
    """When world returns SUCCESS, focus is COMPLETED and the next step is ACTIVE."""
    player = _stubbed_player()
    player.mission.add_sub_mission("Step A")
    player.mission.add_sub_mission("Step B")
    player.mission.steps[0].status = MissionStatus.ACTIVE
    player.input_queue.put_nowait(
        WResComplete(status=WResStatus.SUCCESS, feedback="world confirmed")
    )

    asyncio.run(player.complete(ActionComplete(reason="done", outcome="built the thing")))

    assert player.mission.steps[0].status == MissionStatus.COMPLETED
    assert player.mission.steps[1].status == MissionStatus.ACTIVE


def test_complete_sends_wrec_complete() -> None:
    """Player.complete() sends a WRecComplete to the world queue with correct fields."""
    player = _stubbed_player()
    player.mission.add_sub_mission("Gather 5 logs")
    player.mission.steps[0].status = MissionStatus.ACTIVE
    player.input_queue.put_nowait(WResComplete(status=WResStatus.SUCCESS, feedback="ok"))

    asyncio.run(player.complete(ActionComplete(reason="done", outcome="gathered 5 logs")))

    put_mock: AsyncMock = player.world_input_queue.put  # type: ignore[assignment]
    sent_req = put_mock.call_args[0][0]
    assert isinstance(sent_req, WRecComplete)
    assert sent_req.objective == "Gather 5 logs"
    assert sent_req.outcome == "gathered 5 logs"
