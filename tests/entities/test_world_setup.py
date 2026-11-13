"""Tests for the shared starting world."""

import asyncio
import random

from laife.entities.world_runner import WorldRunner
from laife.entities.world_setup import setup_world


def _build(seed: int) -> WorldRunner:
    """Build the starting world from *seed*.

    Inside a running loop, as in the game: ``alg.log`` starts its task on first use.
    """

    async def _run() -> WorldRunner:
        runner = WorldRunner()
        setup_world(runner, None, random.Random(seed))  # noqa: S311
        return runner

    return asyncio.run(_run())


def test_same_seed_same_world() -> None:
    """Two worlds built from one seed place the players identically."""
    first = [p.position for p in _build(7).players]
    second = [p.position for p in _build(7).players]
    assert first == second


def test_world_has_players_and_buildings() -> None:
    """The starting world holds two players and rejects the colliding house."""
    runner = _build(0)
    assert [p.name for p in runner.players] == ["p0", "p1"]
    assert "Colliding House" not in [b.name for b in runner.buildings]
