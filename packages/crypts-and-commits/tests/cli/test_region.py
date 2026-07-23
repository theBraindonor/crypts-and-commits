from pathlib import Path

import pytest
from typer.testing import CliRunner

from cac.cli import common as cli_common
from cac.cli.app import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_get_missing_region_fails() -> None:
    result = runner.invoke(app, ["region", "get", "missing"])

    assert result.exit_code == 1


def test_get_shows_metadata_and_body() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--path", "src/frontend", "--body", "Body text."])

    result = runner.invoke(app, ["region", "get", "northlands"])

    assert result.exit_code == 0
    assert "name" in result.output
    assert "src/frontend" in result.output
    assert "Body text." in result.output


def test_get_preserves_bracketed_body_text() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "See [tool.pdm.workspace] for details."])

    result = runner.invoke(app, ["region", "get", "northlands"])

    assert result.exit_code == 0
    assert "[tool.pdm.workspace]" in result.output


def test_list_reports_no_region_files() -> None:
    result = runner.invoke(app, ["region", "list"])

    assert result.exit_code == 0
    assert "No region files found." in result.output


def test_create_with_body_option(tmp_path: Path) -> None:
    result = runner.invoke(app, ["region", "create", "northlands", "--body", "# Northlands"])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook" / "region" / "northlands.md").exists()


def test_create_rejects_invalid_name() -> None:
    result = runner.invoke(app, ["region", "create", "bad name", "--body", "text"])

    assert result.exit_code == 1
    assert "invalid" in result.output


def test_create_opens_editor_when_body_omitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli_common.click, "edit", lambda *_args, **_kwargs: "# Edited body")

    result = runner.invoke(app, ["region", "create", "northlands"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "Edited body" in text


def test_list_shows_created_region() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text"])

    result = runner.invoke(app, ["region", "list"])

    assert "northlands" in result.output


def test_update_replaces_body(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "Original"])

    result = runner.invoke(app, ["region", "update", "northlands", "--body", "Updated"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "Updated" in text
    assert "Original" not in text


def test_update_missing_region_fails() -> None:
    result = runner.invoke(app, ["region", "update", "missing", "--body", "text"])

    assert result.exit_code == 1


def test_delete_with_yes_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text"])

    result = runner.invoke(app, ["region", "delete", "northlands", "--yes"])

    assert result.exit_code == 0
    assert not (tmp_path / ".sourcebook" / "region" / "northlands.md").exists()


def test_delete_prompts_without_yes_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text"])

    result = runner.invoke(app, ["region", "delete", "northlands"], input="n\n")

    assert result.exit_code != 0
    assert (tmp_path / ".sourcebook" / "region" / "northlands.md").exists()


def test_delete_missing_region_fails() -> None:
    result = runner.invoke(app, ["region", "delete", "missing", "--yes"])

    assert result.exit_code == 1


def test_create_with_path_option(tmp_path: Path) -> None:
    result = runner.invoke(app, ["region", "create", "frontend", "--path", "src/frontend", "--body", "text"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "region" / "frontend.md").read_text(encoding="utf-8")
    assert "path: src/frontend" in text


def test_set_path_updates_path(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text"])

    result = runner.invoke(app, ["region", "set-path", "northlands", "src/backend"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "path: src/backend" in text


def test_set_path_missing_region_fails() -> None:
    result = runner.invoke(app, ["region", "set-path", "missing", "src/backend"])

    assert result.exit_code == 1
