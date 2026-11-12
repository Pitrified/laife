"""Run the game with no window and no provider; see ``laife.headless``."""

import argparse
import asyncio

from laife.headless import run_headless
from laife.meta.logger import configure_logging


def main() -> None:
    """Parse the turn count and seed, run, and print where the log went."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turns", type=int, default=6, help="turns per player")
    parser.add_argument("--seed", type=int, default=0, help="seed for the starting world")
    args = parser.parse_args()

    log_file = configure_logging(level="INFO")
    runner = asyncio.run(run_headless(turns=args.turns, seed=args.seed))

    print()  # noqa: T201
    for player in runner.players:
        print(f"{player.name}: {player.turn} turns, at {player.position}")  # noqa: T201
    print(f"log: {log_file}")  # noqa: T201


if __name__ == "__main__":
    main()
