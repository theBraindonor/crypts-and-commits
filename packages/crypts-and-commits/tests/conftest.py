from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cac.core import frontmatter_utils, git_utils

FIXED_TIME = datetime(2026, 7, 23, 18, 4, 12, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def identity(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    def _set(*, user: str = "John Hoff", when: datetime = FIXED_TIME) -> None:
        monkeypatch.setattr(git_utils, "current_git_user", lambda root: user)
        monkeypatch.setattr(frontmatter_utils, "utcnow", lambda: when)

    return _set


@pytest.fixture(autouse=True)
def _default_identity(identity: Callable[..., None]) -> None:
    identity()
