import subprocess
from pathlib import Path

import pytest

from cac.core import git_utils


class _Result:
    def __init__(self, returncode: int, stdout: str) -> None:
        self.returncode = returncode
        self.stdout = stdout


def test_current_git_user_returns_configured_name(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Result(0, "John Hoff\n"))

    assert git_utils.current_git_user(tmp_path) == "John Hoff"


def test_current_git_user_raises_when_git_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def _raise(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        git_utils.current_git_user(tmp_path)


def test_current_git_user_raises_on_nonzero_exit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Result(1, ""))

    with pytest.raises(git_utils.GitIdentityError):
        git_utils.current_git_user(tmp_path)


def test_current_git_user_raises_on_blank_name(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _Result(0, "   \n"))

    with pytest.raises(git_utils.GitIdentityError):
        git_utils.current_git_user(tmp_path)
