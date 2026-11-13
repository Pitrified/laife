"""The world snapshot taken from a headless run."""

import asyncio
import json
from typing import TYPE_CHECKING

from laife.headless import run_headless
from laife.meta.logger import configure_logging
from laife.meta.logger import restore_default_logging
from laife.web.snapshot import HISTORY_SHOWN
from laife.web.snapshot import take_snapshot

if TYPE_CHECKING:
    from pathlib import Path


def test_snapshot_of_headless_run_dumps_to_json(tmp_path: Path) -> None:
    """Every player, terrain and building is in the snapshot, and it dumps to JSON."""
    configure_logging(log_file=tmp_path / "game.jsonl", enqueue=False)
    try:
        runner = asyncio.run(asyncio.wait_for(run_headless(turns=3, seed=0), timeout=30))
    finally:
        restore_default_logging()

    snapshot = take_snapshot(runner, None, seq=7)
    dumped = json.loads(snapshot.model_dump_json())

    assert dumped["seq"] == 7
    assert dumped["paused"] is None
    assert len(dumped["terrains"]) == len(runner.terrains)
    assert len(dumped["buildings"]) == len(runner.buildings)
    by_name = {p["name"]: p for p in dumped["players"]}
    for player in runner.players:
        view = by_name[player.name]
        assert view["turn"] == player.turn
        assert tuple(view["position"]) == player.position
        assert view["mission"]["objective"] == player.mission.objective
        assert len(view["history"]) == min(len(player.history.history), HISTORY_SHOWN)
        assert "parent_mission" not in view["mission"]
