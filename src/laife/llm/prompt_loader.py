"""Infrastructure for loading versioned Jinja prompt templates from disk."""

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from pydantic import BaseModel


class PromptLoaderConfig(BaseModel):
    """Configuration for a PromptLoader.

    Attributes:
        base_prompt_fol: Root folder that contains per-prompt subdirectories.
        prompt_name: Name of the prompt subdirectory (e.g. "player_brain").
        version: Explicit version number as a string (e.g. "1"), or "auto" to
            pick the highest available version automatically.
    """

    base_prompt_fol: Path
    prompt_name: str
    version: str = "auto"


class NoPromptVersionFoundError(FileNotFoundError):
    """Raised when no versioned Jinja files are found for a prompt."""

    def __init__(self, prompt_dir: Path) -> None:
        """Initialize with the directory that contained no versioned prompt files."""
        super().__init__(f"No vN.jinja files found in {prompt_dir}")


@dataclass
class PromptLoader:
    """Load a versioned Jinja prompt template from disk.

    Usage::

        config = PromptLoaderConfig(
            base_prompt_fol=paths.prompts_fol,
            prompt_name="player_brain",
        )
        prompt_str = PromptLoader(config).load_prompt()
    """

    config: PromptLoaderConfig
    _prompt_cache: str | None = field(default=None, init=False, repr=False)

    def _resolve_version(self) -> str:
        """Return the effective version string.

        If ``config.version == "auto"``, scans the prompt directory for files
        matching ``vN.jinja`` and returns the identifier of the highest N found.
        Otherwise, returns ``config.version`` as-is.

        Returns:
            Version string (e.g. ``"2"``).

        Raises:
            NoPromptVersionFoundError: When version is "auto" and no matching
                files exist.
        """
        if self.config.version != "auto":
            return self.config.version

        prompt_dir = self.config.base_prompt_fol / self.config.prompt_name
        versions: list[int] = []
        for path in prompt_dir.glob("v*.jinja"):
            stem = path.stem  # e.g. "v3"
            if stem[1:].isdigit():
                versions.append(int(stem[1:]))

        if not versions:
            raise NoPromptVersionFoundError(prompt_dir)

        return str(max(versions))

    def _prompt_path(self) -> Path:
        version = self._resolve_version()
        return self.config.base_prompt_fol / self.config.prompt_name / f"v{version}.jinja"

    def load_prompt(self) -> str:
        """Return the raw Jinja template string, reading from disk on first call.

        The result is cached in-memory so subsequent calls do not incur I/O.

        Returns:
            Raw contents of the resolved ``.jinja`` file.
        """
        if self._prompt_cache is None:
            self._prompt_cache = self._prompt_path().read_text(encoding="utf-8")
        return self._prompt_cache
