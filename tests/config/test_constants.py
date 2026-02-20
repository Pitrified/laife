"""Test the constants file."""

from laife.config.constants import ROOT_FOL


def test_root_is_laife() -> None:
    """Test that the root folder is named 'laife'."""
    assert ROOT_FOL.name == "laife"
