"""Fail when a pre-commit hook runs a different version of a tool than uv.lock holds.

The same tool is installed twice: once by uv into the project environment, once by
pre-commit into its own. When the two versions differ, `make lint` and the commit hook
disagree about the same file. Copied from python-project-template, whose
docs/guides/pre_commit.md, "Tool versions", has why and how to move a tool.

Run from the repository root:

    python3 scripts/check_tool_pins.py

Standard library only, so it runs before `uv sync` and in any environment.
"""

from pathlib import Path
import re
import sys
import tomllib

# Hook repository -> the package uv.lock knows it as. A hooked tool missing here is
# not checked; add it when it is also a dependency.
HOOK_PACKAGES = {
    "https://github.com/astral-sh/ruff-pre-commit": "ruff",
    "https://github.com/RobertCraigie/pyright-python": "pyright",
    "https://github.com/kynan/nbstripout": "nbstripout",
    # The package name reads as a secret keyword to detect-secrets.
    # pragma: allowlist nextline secret
    "https://github.com/Yelp/detect-secrets": "detect-secrets",
}

# A `- repo:` line, then the first `rev:` after it. The config is not parsed as YAML,
# so the check needs no dependency.
REPO_REV = re.compile(
    r"-\s+repo:\s*(\S+)(?:(?!-\s+repo:).)*?\brev:\s*['\"]?v?([^\s'\"]+)", re.DOTALL
)


def hook_versions(config: Path) -> dict[str, str]:
    """Map each checked package to the rev its hook is pinned at."""
    found = {}
    for repo, rev in REPO_REV.findall(config.read_text(encoding="utf-8")):
        if repo in HOOK_PACKAGES:
            found[HOOK_PACKAGES[repo]] = rev
    return found


def locked_versions(lock: Path) -> dict[str, str]:
    """Map each package in uv.lock to its locked version."""
    data = tomllib.loads(lock.read_text(encoding="utf-8"))
    packages = data.get("package", [])
    return {pkg["name"]: pkg["version"] for pkg in packages if "version" in pkg}


def main() -> int:
    """Compare the hook revs with uv.lock and report every mismatch."""
    hooks = hook_versions(Path(".pre-commit-config.yaml"))
    locked = locked_versions(Path("uv.lock"))
    problems = []
    for package, rev in sorted(hooks.items()):
        if package not in locked:
            continue
        if rev != locked[package]:
            lock_version = locked[package]
            problems.append(
                f"{package}: hook rev {rev} in .pre-commit-config.yaml, "
                f"{lock_version} in uv.lock. Pin {package}=={lock_version} in "
                "pyproject.toml and set the hook rev to match, or move both to a new "
                "version together."
            )
    for line in problems:
        print(line, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
