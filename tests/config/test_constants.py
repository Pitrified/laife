"""Test the constants file."""

import tomllib

from laife.config.constants import ROOT_FOL


def test_root_is_project_root() -> None:
    """Test that the root folder holds laife's pyproject.toml.

    Checks the content, not the folder name: a worktree checkout is named
    ``laife-<suffix>`` and is still the project root.
    """
    pyproject = tomllib.loads((ROOT_FOL / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["name"] == "laife"
