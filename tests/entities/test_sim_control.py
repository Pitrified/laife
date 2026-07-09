"""Tests for laife.entities.sim_control."""

import asyncio
from unittest.mock import patch

from laife.entities.sim_control import SimControl
from laife.meta.log_events import EVT_SIM_CONTROL

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _settle() -> None:
    """Let pending tasks advance a few scheduler ticks."""
    for _ in range(5):
        await asyncio.sleep(0)


# ---------------------------------------------------------------------------
# wait_turn - running / paused / resumed
# ---------------------------------------------------------------------------


def test_wait_turn_returns_immediately_while_running() -> None:
    """While running, the gate is transparent - no blocking, no events."""

    async def _run() -> None:
        control = SimControl()
        await asyncio.wait_for(control.wait_turn("Alice", 1), timeout=1)

    asyncio.run(_run())


def test_pause_blocks_and_resume_releases() -> None:
    """After pause() a waiter blocks at the gate; resume() releases it."""

    async def _run() -> None:
        control = SimControl()
        control.pause()
        assert control.paused

        waiter = asyncio.ensure_future(control.wait_turn("Alice", 1))
        await _settle()
        assert not waiter.done()

        control.resume()
        assert not control.paused
        await asyncio.wait_for(waiter, timeout=1)

    asyncio.run(_run())


def test_toggle_flips_between_paused_and_running() -> None:
    """toggle() pauses when running and resumes when paused."""

    async def _run() -> None:
        control = SimControl()
        control.toggle()
        assert control.paused
        control.toggle()
        assert not control.paused

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# step - one permit, one waiter
# ---------------------------------------------------------------------------


def test_step_releases_exactly_one_of_two_waiters() -> None:
    """Each step() while paused lets exactly one blocked player through."""

    async def _run() -> None:
        control = SimControl()
        control.pause()
        waiter_a = asyncio.ensure_future(control.wait_turn("Alice", 1))
        waiter_b = asyncio.ensure_future(control.wait_turn("Bob", 1))
        await _settle()
        assert not waiter_a.done()
        assert not waiter_b.done()

        control.step()
        await _settle()
        assert sum(w.done() for w in (waiter_a, waiter_b)) == 1

        control.step()
        await _settle()
        assert waiter_a.done()
        assert waiter_b.done()

    asyncio.run(_run())


def test_resume_drops_unconsumed_step_permits() -> None:
    """A permit banked while paused must not leak a step into a later pause."""

    async def _run() -> None:
        control = SimControl()
        control.pause()
        control.step()  # no waiter consumes this permit
        control.resume()
        control.pause()

        waiter = asyncio.ensure_future(control.wait_turn("Alice", 1))
        await _settle()
        assert not waiter.done()

        waiter.cancel()

    asyncio.run(_run())


def test_step_is_a_noop_while_running() -> None:
    """step() while running must not bank a permit for a later pause."""

    async def _run() -> None:
        control = SimControl()
        control.step()
        control.pause()

        waiter = asyncio.ensure_future(control.wait_turn("Alice", 1))
        await _settle()
        assert not waiter.done()

        waiter.cancel()

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# struct-log markers
# ---------------------------------------------------------------------------


def test_pause_and_resume_emit_markers() -> None:
    """pause() and resume() each emit EVT_SIM_CONTROL with their state."""

    async def _run() -> None:
        control = SimControl()
        with patch("laife.entities.sim_control.slog") as mock_slog:
            control.pause()
            control.resume()

        states = [call.kwargs["state"] for call in mock_slog.bind.call_args_list]
        assert states == ["paused", "resumed"]
        for call in mock_slog.bind.call_args_list:
            assert call.kwargs["event"] == EVT_SIM_CONTROL

    asyncio.run(_run())


def test_repeated_pause_or_resume_emits_once() -> None:
    """Pausing while paused (or resuming while running) is a silent no-op."""

    async def _run() -> None:
        control = SimControl()
        with patch("laife.entities.sim_control.slog") as mock_slog:
            control.resume()  # already running - no event
            control.pause()
            control.pause()  # already paused - no event

        states = [call.kwargs["state"] for call in mock_slog.bind.call_args_list]
        assert states == ["paused"]

    asyncio.run(_run())


def test_step_marker_carries_the_released_player_and_turn() -> None:
    """The step marker is emitted at consumption with the advancing (player, turn)."""

    async def _run() -> None:
        control = SimControl()
        control.pause()
        waiter = asyncio.ensure_future(control.wait_turn("Alice", 7))
        await _settle()

        with patch("laife.entities.sim_control.slog") as mock_slog:
            control.step()
            await asyncio.wait_for(waiter, timeout=1)

        mock_slog.bind.assert_called_once_with(
            event=EVT_SIM_CONTROL,
            state="step",
            player="Alice",
            turn=7,
        )
        mock_slog.bind.return_value.info.assert_called_once_with(EVT_SIM_CONTROL)

    asyncio.run(_run())
