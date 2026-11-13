"""The ``llm_call`` records made in the world's task carry the right player and turn."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from loguru import logger
import pytest

from laife.entities.player import Player
from laife.entities.world_channel import WRecCraft
from laife.entities.world_channel import WRecInteract
from laife.entities.world_channel import WRes
from laife.entities.world_runner import WorldRunner
from laife.llm.scripted_chat import ScriptedChatConfig
from laife.llm.scripted_chat import default_script
from laife.meta.log_events import EVT_LLM_CALL
from laife.meta.logger import configure_logging
from laife.meta.logger import restore_default_logging

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture
def log_file(tmp_path: Path) -> Generator[Path]:
    """Write the structured log to a temp file, synchronously."""
    path = tmp_path / "game.jsonl"
    configure_logging(level="INFO", log_file=path, enqueue=False)
    yield path
    logger.remove()
    restore_default_logging()


def _llm_calls(log_file: Path) -> list[dict]:
    """Return the extra fields of every llm_call record."""
    rows = [json.loads(line)["record"]["extra"] for line in log_file.read_text().splitlines()]
    return [r for r in rows if r.get("event") == EVT_LLM_CALL]


async def _handle(runner: WorldRunner, req: WRecCraft | WRecInteract) -> WRes:
    """Send *req* through the runner's loop and return its response."""
    task = asyncio.create_task(runner.simulate())
    await runner.input_queue.put(req)
    response = await req.response_queue.get()
    task.cancel()
    return response


def _request[T: WRecCraft | WRecInteract](req: T, player: str, turn: int) -> T:
    """Stamp *req* as Player._world_request does."""
    req.player_name = player
    req.turn = turn
    return req


def test_judge_call_is_logged_as_the_requester(log_file: Path) -> None:
    """A judge's llm_call carries the requesting player and turn."""
    runner = WorldRunner(chat_config=ScriptedChatConfig())
    req = _request(
        WRecCraft(
            response_queue=asyncio.Queue(),
            utensil_name="hammer",
            description="A hammer.",
            observation="",
            player_state="",
        ),
        player="p0",
        turn=3,
    )

    asyncio.run(_handle(runner, req))

    calls = _llm_calls(log_file)
    assert [(c["player"], c["turn"], c["stage"]) for c in calls] == [("p0", 3, "judge_craft")]


def test_reply_is_logged_as_the_replier(log_file: Path) -> None:
    """The reply's llm_call carries the replier's name and turn, not the sender's."""
    runner = WorldRunner(chat_config=ScriptedChatConfig())
    target = Player(
        "p1",
        position=(0, 0),
        player_type="inu",
        world_input_queue=runner.input_queue,
        chat_config=ScriptedChatConfig(script=default_script("p0")),
    )
    target.turn = 5
    runner.add_player(target)
    req = _request(
        WRecInteract(
            response_queue=asyncio.Queue(),
            sender_name="p0",
            sender_prompt="Name: p0",
            target_name="p1",
            message="hi",
        ),
        player="p0",
        turn=2,
    )

    asyncio.run(_handle(runner, req))

    calls = _llm_calls(log_file)
    assert [(c["player"], c["turn"], c["stage"]) for c in calls] == [("p1", 5, "reply")]
