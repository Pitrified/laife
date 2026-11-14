"""Play the live game, served on the world page; see docs/guides/web.md.

Every player turn calls the configured LLM provider and spends credit. The run
starts paused, so nothing is spent until the page resumes it, and it stops
after ``--turns`` turns per player.
"""

import argparse
import asyncio
from contextlib import suppress
import random

from laife.entities.sim_control import SimControl
from laife.entities.world_runner import WorldRunner
from laife.entities.world_setup import setup_world
from laife.meta.logger import configure_logging
from laife.web.run import serve_run
from laife.web.server import DEFAULT_HOST
from laife.web.server import DEFAULT_PORT

LIVE_TURNS = 3
"""Turns per player unless --turns says otherwise; each turn calls the provider."""


async def play(args: argparse.Namespace) -> None:
    """Build the live world and serve it until it is stopped."""
    sim_control = SimControl()
    if args.paused:
        sim_control.pause()
    runner = WorldRunner()
    # Unseeded unless --seed is given; the seed a headless run used gives its starting world.
    setup_world(runner, sim_control, random.Random(args.seed))  # noqa: S311
    await serve_run(runner, sim_control, turns=args.turns or None, host=args.host, port=args.port)


def main() -> None:
    """Parse the options, serve the live game, and say where the log went."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--turns", type=int, default=LIVE_TURNS, help="turns per player; 0 is no limit"
    )
    parser.add_argument("--seed", type=int, default=None, help="seed for the starting world")
    parser.add_argument("--host", default=DEFAULT_HOST, help="address to serve on")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="port to serve on")
    parser.add_argument(
        "--paused",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="start paused, resumed from the page (default); --no-paused starts running",
    )
    args = parser.parse_args()

    log_file = configure_logging(level="INFO")
    state = "paused, resume it from the page" if args.paused else "running"
    print(f"serving on http://{args.host}:{args.port}, {state}; log: {log_file}")  # noqa: T201
    # Ctrl-C ends in KeyboardInterrupt; the quit route returns normally.
    with suppress(KeyboardInterrupt):
        asyncio.run(play(args))
    print("\nstopped")  # noqa: T201


if __name__ == "__main__":
    main()
