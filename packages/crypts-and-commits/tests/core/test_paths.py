from pathlib import Path

import pytest
from cac.core.paths import resolve_project_root


def test_resolve_project_root_returns_cwd_when_sourcebook_is_there(tmp_path: Path) -> None:
    (tmp_path / ".sourcebook").mkdir()

    assert resolve_project_root(tmp_path) == tmp_path


def test_resolve_project_root_walks_up_from_a_nested_subdirectory(tmp_path: Path) -> None:
    (tmp_path / ".sourcebook").mkdir()
    nested = tmp_path / "packages" / "crypts-and-commits"
    nested.mkdir(parents=True)

    assert resolve_project_root(nested) == tmp_path


def test_resolve_project_root_falls_back_to_start_when_no_ancestor_qualifies(tmp_path: Path) -> None:
    nested = tmp_path / "some" / "unbootstrapped" / "place"
    nested.mkdir(parents=True)

    assert resolve_project_root(nested) == nested


def test_resolve_project_root_defaults_to_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".sourcebook").mkdir()
    nested = tmp_path / "packages" / "crypts-and-commits"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    assert resolve_project_root() == tmp_path
