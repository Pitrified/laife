"""Tests for PromptLoader and PromptLoaderConfig."""

from pathlib import Path

import pytest

from laife.llm.prompt_loader import NoPromptVersionFoundError
from laife.llm.prompt_loader import PromptLoader
from laife.llm.prompt_loader import PromptLoaderConfig


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    """Create a temp prompts directory with v1.jinja and v2.jinja."""
    d = tmp_path / "player_brain"
    d.mkdir()
    (d / "v1.jinja").write_text("prompt v1", encoding="utf-8")
    (d / "v2.jinja").write_text("prompt v2", encoding="utf-8")
    return tmp_path


def make_loader(base: Path, *, version: str = "auto") -> PromptLoader:
    """Build a PromptLoader for the given base directory and version."""
    return PromptLoader(
        PromptLoaderConfig(
            base_prompt_fol=base,
            prompt_name="player_brain",
            version=version,
        )
    )


# ---------------------------------------------------------------------------
# version="auto" resolution
# ---------------------------------------------------------------------------


def test_auto_picks_highest_version(prompt_dir: Path) -> None:
    """Auto should resolve to the file with the highest version number."""
    loader = make_loader(prompt_dir)
    assert loader._resolve_version() == "2"


def test_auto_picks_highest_when_only_one_version(tmp_path: Path) -> None:
    """Auto should work with a single file."""
    d = tmp_path / "player_brain"
    d.mkdir()
    (d / "v5.jinja").write_text("only version", encoding="utf-8")
    loader = make_loader(tmp_path)
    assert loader._resolve_version() == "5"


def test_auto_raises_when_no_jinja_files(tmp_path: Path) -> None:
    """Auto should raise NoPromptVersionFoundError if dir is empty."""
    (tmp_path / "player_brain").mkdir()
    loader = make_loader(tmp_path)
    with pytest.raises(NoPromptVersionFoundError):
        loader._resolve_version()


# ---------------------------------------------------------------------------
# explicit version
# ---------------------------------------------------------------------------


def test_explicit_version_returns_as_is(prompt_dir: Path) -> None:
    """Explicit version skips scanning and returns the given string."""
    loader = make_loader(prompt_dir, version="1")
    assert loader._resolve_version() == "1"


def test_explicit_version_loads_correct_file(prompt_dir: Path) -> None:
    """load_prompt with version='1' should return the v1 content."""
    loader = make_loader(prompt_dir, version="1")
    assert loader.load_prompt() == "prompt v1"


def test_auto_loads_highest_content(prompt_dir: Path) -> None:
    """load_prompt with version='auto' should return the v2 content."""
    loader = make_loader(prompt_dir)
    assert loader.load_prompt() == "prompt v2"


# ---------------------------------------------------------------------------
# caching
# ---------------------------------------------------------------------------


def test_load_prompt_caches_result(prompt_dir: Path) -> None:
    """Second call should return the same string without re-reading disk."""
    loader = make_loader(prompt_dir)

    first = loader.load_prompt()
    # Poison the cache to prove the second call does not re-read disk
    loader._prompt_cache = "POISONED"
    second = loader.load_prompt()

    assert first == "prompt v2"
    assert second == "POISONED"  # same cached value, not re-read from disk


def test_cache_is_none_before_first_load(prompt_dir: Path) -> None:
    """_prompt_cache starts as None."""
    loader = make_loader(prompt_dir)
    assert loader._prompt_cache is None


def test_cache_is_set_after_load(prompt_dir: Path) -> None:
    """_prompt_cache is populated after the first load_prompt call."""
    loader = make_loader(prompt_dir)
    loader.load_prompt()
    assert loader._prompt_cache is not None
