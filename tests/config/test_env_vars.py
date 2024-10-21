"""Test that the environment variables are available."""

import os

import pytest


def test_env_vars() -> None:
    """The environment var LAIFE_SAMPLE_ENV_VAR is available."""
    assert "LAIFE_SAMPLE_ENV_VAR" in os.environ
    assert os.environ["LAIFE_SAMPLE_ENV_VAR"] == "sample"
