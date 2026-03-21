"""Unit tests for the structured file logger."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from loguru import logger
import pytest

from laife.meta.log_events import EVT_ACTION
from laife.meta.log_events import EVT_LLM_CALL
from laife.meta.log_events import EVT_WORLD_REQUEST
from laife.meta.logger import configure_logging
from laife.meta.logger import restore_default_logging
from laife.meta.logger import slog

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_logger() -> Generator[None]:
    """Remove all loguru handlers before each test; restore stderr after."""
    logger.remove()
    yield
    restore_default_logging()


# ---------------------------------------------------------------------------
# configure_logging
# ---------------------------------------------------------------------------


def test_configure_logging_creates_file(tmp_path: Path) -> None:
    """configure_logging must create the log file on disk."""
    log_file = tmp_path / "game.jsonl"
    configure_logging(level="INFO", log_file=log_file, enqueue=False)
    slog.info("ping")
    assert log_file.exists()


def test_configure_logging_writes_json_lines(tmp_path: Path) -> None:
    """Each log call must produce exactly one valid JSON line."""
    log_file = tmp_path / "game.jsonl"
    configure_logging(level="INFO", log_file=log_file, enqueue=False)
    slog.bind(event=EVT_ACTION, player="Alice").info(EVT_ACTION)
    slog.bind(event=EVT_LLM_CALL, model="gpt-4o", elapsed=1.23).info(EVT_LLM_CALL)

    lines = log_file.read_text().splitlines()
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # must be valid JSON - raises on failure


def test_configure_logging_extra_fields_in_record(tmp_path: Path) -> None:
    """Bound extra fields must appear inside record.extra in the JSON output."""
    log_file = tmp_path / "game.jsonl"
    configure_logging(level="INFO", log_file=log_file, enqueue=False)
    slog.bind(event=EVT_ACTION, player="Bob").info(EVT_ACTION)

    record = json.loads(log_file.read_text())
    extra = record["record"]["extra"]
    assert extra["event"] == EVT_ACTION
    assert extra["player"] == "Bob"


def test_configure_logging_message_field(tmp_path: Path) -> None:
    """The message field in the JSON record must match the .info() argument."""
    log_file = tmp_path / "game.jsonl"
    configure_logging(level="INFO", log_file=log_file, enqueue=False)
    slog.info(EVT_WORLD_REQUEST)

    record = json.loads(log_file.read_text())
    assert record["record"]["message"] == EVT_WORLD_REQUEST


def test_configure_logging_level_filtering(tmp_path: Path) -> None:
    """DEBUG messages must be suppressed when level is INFO."""
    log_file = tmp_path / "game.jsonl"
    configure_logging(level="INFO", log_file=log_file, enqueue=False)
    slog.bind(event="verbose_debug").debug("verbose_debug")

    content = log_file.read_text() if log_file.exists() else ""
    assert content == ""


def test_configure_logging_debug_level_passes(tmp_path: Path) -> None:
    """DEBUG messages must appear when level is DEBUG."""
    log_file = tmp_path / "game.jsonl"
    configure_logging(level="DEBUG", log_file=log_file, enqueue=False)
    slog.bind(event="verbose_debug").debug("verbose_debug")

    lines = log_file.read_text().splitlines()
    assert len(lines) == 1


def test_configure_logging_auto_timestamp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When log_file is None a timestamped file must be created under cache/."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "cache").mkdir()
    configure_logging(level="INFO", enqueue=False)
    files = list((tmp_path / "cache").glob("game_*.jsonl"))
    assert len(files) == 1


def test_configure_logging_creates_parent_dirs(tmp_path: Path) -> None:
    """configure_logging must create missing parent directories."""
    log_file = tmp_path / "nested" / "dir" / "game.jsonl"
    configure_logging(level="INFO", log_file=log_file, enqueue=False)
    assert log_file.parent.exists()


# ---------------------------------------------------------------------------
# restore_default_logging
# ---------------------------------------------------------------------------


def test_restore_default_logging_adds_stderr_handler() -> None:
    """restore_default_logging must add loguru's stderr handler back."""
    logger.remove()
    restore_default_logging()
    # If stderr handler is active, this should not raise
    logger.info("restored")


def test_no_loguru_stderr_after_configure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """After configure_logging, loguru must not write to stderr."""
    log_file = tmp_path / "game.jsonl"
    configure_logging(level="INFO", log_file=log_file, enqueue=False)
    slog.info("should not appear on stderr")
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""
