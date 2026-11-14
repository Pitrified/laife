"""The live game's entry point, checked without playing: playing calls the provider."""

from pathlib import Path
import subprocess
import sys

LIVE_SCRIPT = Path(__file__).parents[1] / "game" / "main.py"


def test_live_entry_imports_and_lists_its_options() -> None:
    """``game/main.py --help`` runs, so every import resolves, and shows the run's options."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(LIVE_SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    for option in ("--turns", "--seed", "--host", "--port", "--no-paused"):
        assert option in result.stdout
