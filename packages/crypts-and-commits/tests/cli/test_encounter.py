from pathlib import Path

import pytest
from typer.testing import CliRunner

from cac.cli import common as cli_common
from cac.cli.app import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def _create_campaign(name: str = "opening-gambit") -> None:
    runner.invoke(app, ["campaign", "create", name, "--body", "text"])


def test_list_reports_no_encounter_files() -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "list", "opening-gambit"])

    assert result.exit_code == 0
    assert "No encounter files found." in result.output


def test_create_requires_existing_campaign() -> None:
    result = runner.invoke(app, ["encounter", "create", "missing", "goblin-ambush", "--body", "text"])

    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_create_with_body_option(tmp_path: Path) -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "create", "opening-gambit", "goblin-ambush", "--body", "# Ambush"])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").exists()


def test_create_rejects_invalid_name() -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "create", "opening-gambit", "bad name", "--body", "text"])

    assert result.exit_code == 1
    assert "invalid" in result.output


def test_create_opens_editor_when_body_omitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _create_campaign()
    monkeypatch.setattr(cli_common.click, "edit", lambda *_args, **_kwargs: "## Requirements\n\nEdited body")

    result = runner.invoke(app, ["encounter", "create", "opening-gambit", "goblin-ambush"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "Edited body" in text


def test_list_shows_created_encounter() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "opening-gambit", "goblin-ambush", "--body", "text"])

    result = runner.invoke(app, ["encounter", "list", "opening-gambit"])

    assert "goblin-ambush" in result.output


def test_update_replaces_body(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "opening-gambit", "goblin-ambush", "--body", "Original"])

    result = runner.invoke(app, ["encounter", "update", "opening-gambit", "goblin-ambush", "--body", "Updated"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "Updated" in text
    assert "Original" not in text


def test_update_missing_encounter_fails() -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "update", "opening-gambit", "missing", "--body", "text"])

    assert result.exit_code == 1


def test_delete_with_yes_flag(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "opening-gambit", "goblin-ambush", "--body", "text"])

    result = runner.invoke(app, ["encounter", "delete", "opening-gambit", "goblin-ambush", "--yes"])

    assert result.exit_code == 0
    assert not (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").exists()


def test_delete_missing_encounter_fails() -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "delete", "opening-gambit", "missing", "--yes"])

    assert result.exit_code == 1


def test_set_status_updates_status(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "opening-gambit", "goblin-ambush", "--body", "text"])

    result = runner.invoke(app, ["encounter", "set-status", "opening-gambit", "goblin-ambush", "abandoned"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "status: abandoned" in text


def test_set_status_rejects_invalid_status() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "opening-gambit", "goblin-ambush", "--body", "text"])

    result = runner.invoke(app, ["encounter", "set-status", "opening-gambit", "goblin-ambush", "cancelled"])

    assert result.exit_code == 1
    assert "invalid" in result.output


def test_assign_region_sets_region(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["region", "create", "northlands", "--body", "text"])
    runner.invoke(app, ["encounter", "create", "opening-gambit", "goblin-ambush", "--body", "text"])

    result = runner.invoke(app, ["encounter", "assign-region", "opening-gambit", "goblin-ambush", "northlands"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "region: northlands" in text
    region_text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "goblin-ambush" not in region_text


def test_assign_region_missing_region_fails() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "opening-gambit", "goblin-ambush", "--body", "text"])

    result = runner.invoke(app, ["encounter", "assign-region", "opening-gambit", "goblin-ambush", "missing"])

    assert result.exit_code == 1


def test_unassign_region_clears_region(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["region", "create", "northlands", "--body", "text"])
    runner.invoke(app, ["encounter", "create", "opening-gambit", "goblin-ambush", "--body", "text"])
    runner.invoke(app, ["encounter", "assign-region", "opening-gambit", "goblin-ambush", "northlands"])

    result = runner.invoke(app, ["encounter", "unassign-region", "opening-gambit", "goblin-ambush"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "region: null" in text
