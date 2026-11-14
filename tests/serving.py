"""Start ``game/headless.py --serve`` as a separate process, for tests that need a real one.

Not a test module: imported by the stop tests and the browser tests.
"""

from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx

HEADLESS_SCRIPT = Path(__file__).parents[1] / "game" / "headless.py"
STARTUP_SECONDS = 30
"""How long a server may take to answer its first request; a fresh process imports everything."""


def free_port() -> int:
    """Return a port that was free a moment ago on localhost."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_serving(cwd: Path, port: int, *flags: str) -> subprocess.Popen[str]:
    """Start an endless serving run on *port*, its log under *cwd*, with extra *flags*."""
    return subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            str(HEADLESS_SCRIPT),
            "--serve",
            "--turns",
            "0",
            "--port",
            str(port),
            *flags,
        ],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def wait_until_up(base_url: str) -> None:
    """Poll ``/state`` until the server answers, for at most ``STARTUP_SECONDS``."""
    deadline = time.monotonic() + STARTUP_SECONDS
    while True:
        try:
            httpx.get(f"{base_url}/state")
        except httpx.TransportError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.1)
        else:
            return
