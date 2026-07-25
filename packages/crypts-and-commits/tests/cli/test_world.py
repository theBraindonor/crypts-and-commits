from pathlib import Path

import pytest
from typer.testing import CliRunner

from cac.cli import common as cli_common
from cac.cli.app import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_get_missing_world_fails() -> None:
    result = runner.invoke(app, ["world", "get"])

    assert result.exit_code == 1


def test_get_shows_metadata_and_body() -> None:
    runner.invoke(app, ["bootstrap", "init"])

    result = runner.invoke(app, ["world", "get"])

    assert result.exit_code == 0
    assert "name" in result.output
    assert "Be sure to edit this world definition file before starting development!" in result.output


def test_get_preserves_bracketed_body_text(tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["world", "set-body", "--body", "See [tool.pdm.workspace] for details."])

    result = runner.invoke(app, ["world", "get"])

    assert result.exit_code == 0
    assert "[tool.pdm.workspace]" in result.output


def test_set_updates_frontmatter_attribute(tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])

    result = runner.invoke(app, ["world", "set", "name", "my-project"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "world.md").read_text(encoding="utf-8")
    assert "name: my-project" in text


def test_set_missing_world_fails() -> None:
    result = runner.invoke(app, ["world", "set", "name", "my-project"])

    assert result.exit_code == 1


def test_set_body_with_body_option(tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])

    result = runner.invoke(app, ["world", "set-body", "--body", "New content."])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "world.md").read_text(encoding="utf-8")
    assert "New content." in text
    assert "This world has not been described yet." not in text


def test_set_body_opens_editor_when_body_omitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    monkeypatch.setattr(cli_common.click, "edit", lambda *_args, **_kwargs: "Edited content.")

    result = runner.invoke(app, ["world", "set-body"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "world.md").read_text(encoding="utf-8")
    assert "Edited content." in text


def test_set_body_missing_world_fails() -> None:
    result = runner.invoke(app, ["world", "set-body", "--body", "text"])

    assert result.exit_code == 1


def test_get_truncates_body_over_budget(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["world", "set-body", "--body", "x" * 200])
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 50)

    result = runner.invoke(app, ["world", "get"])

    assert result.exit_code == 0
    assert "[TRUNCATED" in result.output
    assert str(tmp_path / ".sourcebook" / "world.md") in result.output
