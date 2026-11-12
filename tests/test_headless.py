"""The minimal headless run: it ends, and every player played every turn.

Headless mode is a development tool; this only keeps the run from breaking.
Which actions a run takes is the script's business and is not asserted.
"""

import asyncio
import json
from typing import TYPE_CHECKING

from laife.headless import run_headless
from laife.llm.scripted_chat import default_script
from laife.meta.log_events import EVT_ACTION
from laife.meta.log_events import EVT_WORLD_RESPONSE
from laife.meta.logger import configure_logging
from laife.meta.logger import restore_default_logging

if TYPE_CHECKING:
    from pathlib import Path

# One full pass of the script, so every action type runs once.
TURNS = len(default_script("p1"))


def test_headless_run_ends_with_every_turn_played(tmp_path: Path) -> None:
    """A scripted run returns, logs one action per player turn, and no world error."""
    log_file = configure_logging(log_file=tmp_path / "game.jsonl", enqueue=False)
    try:
        runner = asyncio.run(asyncio.wait_for(run_headless(turns=TURNS, seed=0), timeout=30))
    finally:
        restore_default_logging()

    assert [p.turn for p in runner.players] == [TURNS] * len(runner.players)
    lines = log_file.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line)["record"]["extra"] for line in lines]
    actions = [r for r in records if r.get("event") == EVT_ACTION]
    assert len(actions) == TURNS * len(runner.players)
    errors = [
        r for r in records if r.get("event") == EVT_WORLD_RESPONSE and r.get("status") == "error"
    ]
    assert errors == []
