from pathlib import Path

from cac.core import bootstrap


def test_initialize_creates_sourcebook_directory(tmp_path: Path) -> None:
    sourcebook_dir, created = bootstrap.initialize(tmp_path)

    assert created is True
    assert sourcebook_dir == tmp_path / ".sourcebook"
    assert sourcebook_dir.is_dir()


def test_initialize_is_idempotent(tmp_path: Path) -> None:
    bootstrap.initialize(tmp_path)

    sourcebook_dir, created = bootstrap.initialize(tmp_path)

    assert created is False
    assert sourcebook_dir.is_dir()
