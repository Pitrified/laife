"""Run the game with no window and no provider; see ``laife.headless``."""

import argparse
import asyncio
from contextlib import suppress

from laife.headless import run_headless
from laife.headless import serve_headless
from laife.meta.logger import configure_logging
from laife.web.server import DEFAULT_HOST
from laife.web.server import DEFAULT_PORT

SERVE_PACE = 1.0
"""Seconds per scripted answer when serving, unless --pace says otherwise."""


def main() -> None:
    """Parse the options, run or serve, and print where the log went."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--turns", type=int, default=6, help="turns per player; 0 is no limit when serving"
    )
    parser.add_argument("--seed", type=int, default=0, help="seed for the starting world")
    parser.add_argument(
        "--serve", action="store_true", help="serve the world over HTTP until Ctrl-C"
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="address to serve on")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="port to serve on")
    parser.add_argument(
        "--pace",
        type=float,
        default=None,
        help=f"seconds per scripted answer when serving (default {SERVE_PACE})",
    )
    parser.add_argument("--paused", action="store_true", help="start paused when serving")
    args = parser.parse_args()

    log_file = configure_logging(level="INFO")
    if args.serve:
        print(f"serving on http://{args.host}:{args.port}, log: {log_file}")  # noqa: T201
        # Ctrl-C ends in KeyboardInterrupt; the quit route returns normally.
        with suppress(KeyboardInterrupt):
            asyncio.run(
                serve_headless(
                    turns=args.turns or None,
                    seed=args.seed,
                    pace=SERVE_PACE if args.pace is None else args.pace,
                    paused=args.paused,
                    host=args.host,
                    port=args.port,
                )
            )
        print("\nstopped")  # noqa: T201
        return

    runner = asyncio.run(run_headless(turns=args.turns, seed=args.seed))

    print()  # noqa: T201
    for player in runner.players:
        print(f"{player.name}: {player.turn} turns, at {player.position}")  # noqa: T201
    print(f"log: {log_file}")  # noqa: T201


if __name__ == "__main__":
    main()
