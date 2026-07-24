import subprocess
from pathlib import Path


class GitIdentityError(RuntimeError):
    """Raised when the current git user.name cannot be resolved."""


def current_git_user(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            cwd=root,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise GitIdentityError("git is not installed or not on PATH; cannot resolve the current git user.") from exc

    name = result.stdout.strip()
    if result.returncode != 0 or not name:
        raise GitIdentityError(
            "git user.name is not configured; run 'git config user.name \"Your Name\"' "
            "(locally or --global) before touching an encounter."
        )
    return name
