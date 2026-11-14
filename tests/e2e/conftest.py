"""Fixtures for the browser tests: a serving run in its own process, and Chromium.

Every test in this folder carries the ``e2e`` marker, so ``make check`` skips
them and ``make e2e`` runs only them. Chromium is Playwright's own, from
``~/.cache/ms-playwright``.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from playwright.sync_api import sync_playwright
import pytest

from tests.serving import free_port
from tests.serving import start_serving
from tests.serving import wait_until_up

if TYPE_CHECKING:
    from collections.abc import Iterator
    import subprocess

    from playwright.sync_api import Browser


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every test in this folder as e2e."""
    for item in items:
        if Path(str(item.fspath)).parent == Path(__file__).parent:
            item.add_marker(pytest.mark.e2e)


class ServedRun:
    """A paused, endless serving run and where to reach it."""

    def __init__(self, proc: subprocess.Popen[str], base_url: str) -> None:
        """Hold the process and its URL."""
        self.proc = proc
        self.base_url = base_url


@pytest.fixture
def served_run(tmp_path: Path) -> Iterator[ServedRun]:
    """Start a paused run, quickly paced, on a free port; kill it if a test leaves it running."""
    port = free_port()
    proc = start_serving(tmp_path, port, "--paused", "--pace", "0.05")
    base_url = f"http://127.0.0.1:{port}"
    try:
        wait_until_up(base_url)
        yield ServedRun(proc, base_url)
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.communicate()


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """Headless Chromium for the session."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        yield browser
        browser.close()
