"""Test the constants file."""

import pytest

from laife.constants import ROOT_FOL


def test_root_is_laife() -> None:
    """Test that the root folder is named 'laife'."""
    assert ROOT_FOL.name == "laife"
