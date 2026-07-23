from pathlib import Path

import pytest
from typer.testing import CliRunner

from cac.cli.app import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_init_creates_sourcebook_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook").is_dir()


def test_init_shows_splash() -> None:
    result = runner.invoke(app, ["bootstrap", "init"])

    assert "Crypts And Commits" in result.output
    assert "A Code Assistant Continuity Framework" in result.output
