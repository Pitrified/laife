"""Structured file logger using loguru.

``Alog`` (``src/laife/ui/alog.py``) remains the real-time console feedback
channel.  This module adds a JSON-lines file sink alongside it - one JSON
object per line, written asynchronously so the game loop is not blocked.

Usage
-----
Call ``configure_logging()`` once at startup (before the asyncio loop)::

    from laife.meta.logger import configure_logging, slog
    configure_logging(level="INFO")

At call sites::

    from laife.meta.logger import slog
    from laife.meta.log_events import EVT_ACTION

    slog.bind(event=EVT_ACTION, player="Alice", action="build").info(EVT_ACTION)
"""

from collections.abc import Iterator
from contextlib import contextmanager
import datetime
from pathlib import Path
import sys
import time
import warnings

from loguru import logger

from laife.meta.log_events import EVT_LLM_CALL

# Module-level bound logger.  Import ``slog`` at call sites; never import
# ``logger`` from loguru directly so that all structured calls flow through
# this single configured instance.
slog = logger.bind(logger_name="laife")


@contextmanager
def timed_llm_call(*, player: str, turn: int, model: str, stage: str) -> Iterator[None]:
    """Time an LLM network call and emit one ``EVT_LLM_CALL`` record on exit.

    Wrap the awaited chain call so every LLM round trip - action, plan, reply,
    mission - reports its latency uniformly::

        with timed_llm_call(player=name, turn=turn, model=model, stage="plan"):
            result = await chain.ainvoke(...)

    ``stage`` distinguishes the call site (``action``/``plan``/``reply``/
    ``mission``).  If the wrapped call raises, no record is emitted - only
    completed calls are timed, matching the original inline sites.
    """
    t0 = time.monotonic()
    yield
    slog.bind(
        event=EVT_LLM_CALL,
        player=player,
        turn=turn,
        model=model,
        stage=stage,
        elapsed=round(time.monotonic() - t0, 3),
    ).info(EVT_LLM_CALL)


def configure_logging(
    level: str = "INFO",
    log_file: str | Path | None = None,
    *,
    enqueue: bool = True,
) -> None:
    """Set up the JSON-lines file sink.

    Removes loguru's default stderr handler (``Alog`` handles console output)
    and adds a single file handler that writes one JSON object per line.

    Parameters
    ----------
    level:
        Minimum log level forwarded to the file sink (``"DEBUG"``,
        ``"INFO"``, ``"WARNING"``...).
    log_file:
        Path to the ``.jsonl`` output file.  If *None*, a timestamped file
        is created under ``cache/`` relative to the current working directory
        (e.g. ``cache/game_20260301T120000.jsonl``).
    enqueue:
        When *True* (default) writes are non-blocking via a background thread.
        Set to *False* in tests to get synchronous, immediately-visible output.
    """
    _suppress_known_warnings()

    # Remove all existing handlers (including loguru's default stderr sink)
    # so structured output goes only to the file.
    logger.remove()

    if log_file is None:
        stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S")
        log_file = Path("cache") / f"game_{stamp}.jsonl"

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_file),
        serialize=True,
        level=level,
        enqueue=enqueue,
    )


def _suppress_known_warnings() -> None:
    """Silence upstream-only warnings that are noise on every ``make run``.

    Pydantic serializer warning from ``with_structured_output``: langchain-openai's
    ``_create_chat_result`` (``langchain_openai/chat_models/base.py``) calls
    ``response.model_dump()`` on a completion whose ``parsed`` field is declared
    ``Optional[None]`` but is populated with our parsed model, so pydantic warns
    ``Expected `none` ... [field_name='parsed']``. It is benign (the parsed action
    is returned correctly) and fires entirely inside langchain, not our code or
    llm-core. Remove this filter once langchain-openai stops dumping the raw
    completion with the mismatched ``parsed`` type. See
    scratch_space/35_interaction_error/03_serializer_warning.md.
    """
    warnings.filterwarnings(
        "ignore",
        message="Pydantic serializer warnings",
        category=UserWarning,
        module=r"pydantic\.main",
    )


def restore_default_logging() -> None:
    """Restore loguru to its default stderr handler.

    Intended for use in tests and development utilities where the full
    ``configure_logging`` setup is not desired.
    """
    logger.remove()
    logger.add(sys.stderr)
