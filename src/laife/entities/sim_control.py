"""SimControl - pause / resume / single-step gating for the simulation loop.

Pure asyncio, no pygame dependency (same discipline as ``WorldRunner``).
Players await :meth:`SimControl.wait_turn` at the top of each ``play()``
iteration; the world runner is never gated, so a turn already in flight
(LLM calls and world round trip included) always finishes before its
player blocks. See ``scratch_space/32_observability/03_loop_pause.md``.
"""

import asyncio

from laife.meta.log_events import EVT_SIM_CONTROL
from laife.meta.logger import slog


class SimControl:
    """Gate player turns so the simulation can be paused, resumed, and stepped.

    The trigger methods (:meth:`pause`, :meth:`resume`, :meth:`toggle`,
    :meth:`step`) are synchronous so the pygame event pump can call them
    directly; waiters are woken through a single pulsed ``asyncio.Event``
    rather than an ``asyncio.Condition``, whose ``notify_all`` would need
    the lock held (an ``async with``) and so could not be driven from
    synchronous code.
    """

    def __init__(self) -> None:
        """Start in the running state with no step permits."""
        self._running = True
        self._step_permits = 0
        # Pulsed on every state change; waiters re-check state after waking.
        self._wake = asyncio.Event()

    @property
    def paused(self) -> bool:
        """Return True while the simulation is held at the turn gate."""
        return not self._running

    async def wait_turn(self, player: str, turn: int) -> None:
        """Block *player* before its next turn while paused.

        Returns immediately while running. While paused, waits until
        resumed or a step permit is available; consuming a permit emits
        the ``step`` marker with the ``(player, turn)`` being released,
        so the log records which player advanced.
        """
        while True:
            if self._running:
                return
            if self._step_permits > 0:
                self._step_permits -= 1
                slog.bind(
                    event=EVT_SIM_CONTROL,
                    state="step",
                    player=player,
                    turn=turn,
                ).info(EVT_SIM_CONTROL)
                return
            self._wake.clear()
            await self._wake.wait()

    def pause(self) -> None:
        """Hold every player at the turn gate; in-flight turns still finish."""
        if not self._running:
            return
        self._running = False
        slog.bind(event=EVT_SIM_CONTROL, state="paused").info(EVT_SIM_CONTROL)

    def resume(self) -> None:
        """Release the turn gate and let every player run freely again.

        Unconsumed step permits are dropped so they cannot leak a spurious
        step into a later pause.
        """
        if self._running:
            return
        self._running = True
        self._step_permits = 0
        slog.bind(event=EVT_SIM_CONTROL, state="resumed").info(EVT_SIM_CONTROL)
        self._wake.set()

    def toggle(self) -> None:
        """Flip between running and paused (keybinding convenience)."""
        if self._running:
            self.pause()
        else:
            self.resume()

    def step(self) -> None:
        """Release exactly one blocked player for one full turn; no-op unless paused."""
        if self._running:
            return
        self._step_permits += 1
        self._wake.set()
