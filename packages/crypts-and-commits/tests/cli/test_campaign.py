from pathlib import Path

import pytest
from typer.testing import CliRunner

from cac.cli import common as cli_common
from cac.cli.app import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_get_missing_campaign_fails() -> None:
    result = runner.invoke(app, ["campaign", "get", "missing"])

    assert result.exit_code == 1


def test_get_shows_metadata_and_body() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body text."])

    result = runner.invoke(app, ["campaign", "get", "opening-gambit"])

    assert result.exit_code == 0
    assert "name" in result.output
    assert "status" in result.output
    assert "Body text." in result.output


def test_get_preserves_bracketed_body_text() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "See [tool.pdm.workspace] for details."])

    result = runner.invoke(app, ["campaign", "get", "opening-gambit"])

    assert result.exit_code == 0
    assert "[tool.pdm.workspace]" in result.output


def test_list_reports_no_campaign_files() -> None:
    result = runner.invoke(app, ["campaign", "list"])

    assert result.exit_code == 0
    assert "No campaign files found." in result.output


def test_create_with_body_option(tmp_path: Path) -> None:
    result = runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "# Opening Gambit"])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").exists()


def test_create_rejects_invalid_name() -> None:
    result = runner.invoke(app, ["campaign", "create", "bad name", "--body", "text"])

    assert result.exit_code == 1
    assert "invalid" in result.output


def test_create_opens_editor_when_body_omitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli_common.click, "edit", lambda *_args, **_kwargs: "# Edited body")

    result = runner.invoke(app, ["campaign", "create", "opening-gambit"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").read_text(encoding="utf-8")
    assert "Edited body" in text


def test_list_shows_created_campaign() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["campaign", "list"])

    assert "opening-gambit" in result.output


def test_update_replaces_body(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Original"])

    result = runner.invoke(app, ["campaign", "update", "opening-gambit", "--body", "Updated"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").read_text(encoding="utf-8")
    assert "Updated" in text
    assert "Original" not in text


def test_update_missing_campaign_fails() -> None:
    result = runner.invoke(app, ["campaign", "update", "missing", "--body", "text"])

    assert result.exit_code == 1


def test_delete_with_yes_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["campaign", "delete", "opening-gambit", "--yes"])

    assert result.exit_code == 0
    assert not (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").exists()


def test_delete_prompts_without_yes_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["campaign", "delete", "opening-gambit"], input="n\n")

    assert result.exit_code != 0
    assert (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").exists()


def test_delete_missing_campaign_fails() -> None:
    result = runner.invoke(app, ["campaign", "delete", "missing", "--yes"])

    assert result.exit_code == 1


def test_set_status_updates_status(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["campaign", "set-status", "opening-gambit", "open"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").read_text(encoding="utf-8")
    assert "status: open" in text


def test_set_status_rejects_invalid_status(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["campaign", "set-status", "opening-gambit", "cancelled"])

    assert result.exit_code == 1
    assert "invalid" in result.output


def test_set_status_missing_campaign_fails() -> None:
    result = runner.invoke(app, ["campaign", "set-status", "missing", "open"])

    assert result.exit_code == 1
