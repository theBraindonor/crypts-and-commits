from pathlib import Path

import pytest
from typer.testing import CliRunner

from cac.cli import common as cli_common
from cac.cli.app import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_get_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "get", "missing"])

    assert result.exit_code == 1


def test_get_shows_metadata_and_body() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "Body text."])

    result = runner.invoke(app, ["lore", "get", "conventions"])

    assert result.exit_code == 0
    assert "name" in result.output
    assert "enabled" in result.output
    assert "Body text." in result.output


def test_list_reports_no_lore_files() -> None:
    result = runner.invoke(app, ["lore", "list"])

    assert result.exit_code == 0
    assert "No lore files found." in result.output


def test_create_with_body_option(tmp_path: Path) -> None:
    result = runner.invoke(app, ["lore", "create", "conventions", "--body", "# Conventions"])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook" / "lore" / "conventions.md").exists()


def test_create_rejects_invalid_name() -> None:
    result = runner.invoke(app, ["lore", "create", "bad name", "--body", "text"])

    assert result.exit_code == 1
    assert "invalid" in result.output


def test_create_opens_editor_when_body_omitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli_common.click, "edit", lambda *_args, **_kwargs: "# Edited body")

    result = runner.invoke(app, ["lore", "create", "conventions"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "Edited body" in text


def test_list_shows_created_lore() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])

    result = runner.invoke(app, ["lore", "list"])

    assert "conventions" in result.output


def test_update_replaces_body(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "Original"])

    result = runner.invoke(app, ["lore", "update", "conventions", "--body", "Updated"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "Updated" in text
    assert "Original" not in text


def test_update_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "update", "missing", "--body", "text"])

    assert result.exit_code == 1


def test_delete_with_yes_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])

    result = runner.invoke(app, ["lore", "delete", "conventions", "--yes"])

    assert result.exit_code == 0
    assert not (tmp_path / ".sourcebook" / "lore" / "conventions.md").exists()


def test_delete_prompts_without_yes_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])

    result = runner.invoke(app, ["lore", "delete", "conventions"], input="n\n")

    assert result.exit_code != 0
    assert (tmp_path / ".sourcebook" / "lore" / "conventions.md").exists()


def test_delete_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "delete", "missing", "--yes"])

    assert result.exit_code == 1


def test_assign_links_lore_to_world(tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])

    result = runner.invoke(app, ["lore", "assign-world", "conventions"])

    assert result.exit_code == 0
    world_text = (tmp_path / ".sourcebook" / "world.md").read_text(encoding="utf-8")
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "conventions" in world_text
    assert "assigned_to_world: true" in lore_text


def test_assign_missing_lore_fails() -> None:
    runner.invoke(app, ["bootstrap", "init"])

    result = runner.invoke(app, ["lore", "assign-world", "missing"])

    assert result.exit_code == 1


def test_assign_without_world_fails() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])

    result = runner.invoke(app, ["lore", "assign-world", "conventions"])

    assert result.exit_code == 1


def test_unassign_clears_link(tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])
    runner.invoke(app, ["lore", "assign-world", "conventions"])

    result = runner.invoke(app, ["lore", "unassign-world", "conventions"])

    assert result.exit_code == 0
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "assigned_to_world: false" in lore_text


def test_assign_region_links_lore_to_region(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text"])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])

    result = runner.invoke(app, ["lore", "assign-region", "conventions", "northlands"])

    assert result.exit_code == 0
    region_text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "conventions" in region_text
    assert "northlands" in lore_text


def test_assign_region_missing_lore_fails() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text"])

    result = runner.invoke(app, ["lore", "assign-region", "missing", "northlands"])

    assert result.exit_code == 1


def test_assign_region_missing_region_fails() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])

    result = runner.invoke(app, ["lore", "assign-region", "conventions", "missing"])

    assert result.exit_code == 1


def test_unassign_region_clears_link(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text"])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])
    runner.invoke(app, ["lore", "assign-region", "conventions", "northlands"])

    result = runner.invoke(app, ["lore", "unassign-region", "conventions", "northlands"])

    assert result.exit_code == 0
    region_text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "conventions" not in region_text
    assert "assigned_regions: []" in lore_text


def test_enable_sets_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])
    runner.invoke(app, ["lore", "disable", "conventions"])

    result = runner.invoke(app, ["lore", "enable", "conventions"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "enabled: true" in text


def test_disable_sets_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])

    result = runner.invoke(app, ["lore", "disable", "conventions"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "enabled: false" in text


def test_enable_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "enable", "missing"])

    assert result.exit_code == 1


def test_disable_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "disable", "missing"])

    assert result.exit_code == 1
