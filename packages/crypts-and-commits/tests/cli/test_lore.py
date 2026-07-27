from pathlib import Path

import pytest
from cac.cli import common as cli_common
from cac.cli.app import app
from cac.core import git_utils
from typer.testing import CliRunner

runner = CliRunner()


def _break_git_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("git user.name is not configured.")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_get_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "get", "missing"])

    assert result.exit_code == 1


def test_get_shows_metadata_and_body() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "Body text.", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "get", "conventions"])

    assert result.exit_code == 0
    assert "name" in result.output
    assert "enabled" in result.output
    assert "Body text." in result.output


def test_get_preserves_bracketed_body_text() -> None:
    runner.invoke(
        app,
        ["lore", "create", "conventions", "--body", "See [tool.pdm.workspace] for details.", "--summary", "Summary."],
    )

    result = runner.invoke(app, ["lore", "get", "conventions"])

    assert result.exit_code == 0
    assert "[tool.pdm.workspace]" in result.output


def test_get_shows_placeholder_when_summary_absent(tmp_path: Path) -> None:
    # Summary is mandatory on create, so a summary-less entry can only exist as a
    # legacy/hand-written file; seed one directly to exercise the placeholder path.
    lore_dir = tmp_path / ".sourcebook" / "lore"
    lore_dir.mkdir(parents=True)
    (lore_dir / "conventions.md").write_text(
        "---\nname: conventions\nenabled: true\n---\n\nBody text.\n", encoding="utf-8"
    )

    result = runner.invoke(app, ["lore", "get", "conventions"])

    assert result.exit_code == 0
    assert "No summary has been set" in result.output


def test_create_stores_summary_shown_in_get() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "Body text.", "--summary", "A routing signal."])

    result = runner.invoke(app, ["lore", "get", "conventions"])

    assert result.exit_code == 0
    assert "A routing signal." in result.output


def test_set_summary_then_get_shows_it() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "Body text.", "--summary", "Summary."])

    set_result = runner.invoke(app, ["lore", "set-summary", "conventions", "A brief routing signal."])
    get_result = runner.invoke(app, ["lore", "get", "conventions"])

    assert set_result.exit_code == 0
    assert get_result.exit_code == 0
    assert "A brief routing signal." in get_result.output


def test_get_preserves_bracketed_summary_text() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "Body text.", "--summary", "Summary."])
    runner.invoke(app, ["lore", "set-summary", "conventions", "Covers [tool.pdm.workspace] config."])

    result = runner.invoke(app, ["lore", "get", "conventions"])

    assert result.exit_code == 0
    assert "[tool.pdm.workspace]" in result.output


def test_set_summary_rejects_value_over_cap() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "set-summary", "conventions", "x" * 501])

    assert result.exit_code == 1
    assert "maximum of 500" in result.output


def test_set_summary_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["lore", "set-summary", "conventions", "New summary."])

    assert result.exit_code == 1


def test_set_summary_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "set-summary", "missing", "text"])

    assert result.exit_code == 1


def test_list_reports_no_lore_files() -> None:
    result = runner.invoke(app, ["lore", "list"])

    assert result.exit_code == 0
    assert "No lore files found." in result.output


def test_create_with_body_option(tmp_path: Path) -> None:
    result = runner.invoke(app, ["lore", "create", "conventions", "--body", "# Conventions", "--summary", "Summary."])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook" / "lore" / "conventions.md").exists()


def test_create_requires_summary(tmp_path: Path) -> None:
    result = runner.invoke(app, ["lore", "create", "conventions", "--body", "text"])

    assert result.exit_code == 1
    assert "summary is required" in result.output
    assert not (tmp_path / ".sourcebook" / "lore" / "conventions.md").exists()


def test_create_rejects_over_cap_summary(tmp_path: Path) -> None:
    result = runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "x" * 501])

    assert result.exit_code == 1
    assert "maximum of 500" in result.output
    assert not (tmp_path / ".sourcebook" / "lore" / "conventions.md").exists()


def test_create_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])

    assert result.exit_code == 1


def test_create_rejects_invalid_name() -> None:
    result = runner.invoke(app, ["lore", "create", "bad name", "--body", "text", "--summary", "Summary."])

    assert result.exit_code == 1
    assert "invalid" in result.output


def test_create_opens_editor_when_body_omitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli_common.click, "edit", lambda *_args, **_kwargs: "# Edited body")

    result = runner.invoke(app, ["lore", "create", "conventions", "--summary", "Summary."])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "Edited body" in text


def test_list_shows_created_lore() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "list"])

    assert "conventions" in result.output


def test_update_replaces_body(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "Original", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "update", "conventions", "--body", "Updated", "--summary", "Summary."])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "Updated" in text
    assert "Original" not in text


def test_update_regenerates_summary() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "Original", "--summary", "Old summary."])

    update_result = runner.invoke(
        app, ["lore", "update", "conventions", "--body", "Updated", "--summary", "New summary."]
    )
    get_result = runner.invoke(app, ["lore", "get", "conventions"])

    assert update_result.exit_code == 0
    assert "New summary." in get_result.output
    assert "Updated" in get_result.output


def test_update_requires_summary(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "Original", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "update", "conventions", "--body", "Updated"])

    assert result.exit_code == 1
    assert "summary is required" in result.output
    # The rejected update must not have touched the stored body.
    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "Original" in text
    assert "Updated" not in text


def test_update_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "Original", "--summary", "Summary."])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["lore", "update", "conventions", "--body", "Updated", "--summary", "Summary."])

    assert result.exit_code == 1


def test_update_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "update", "missing", "--body", "text", "--summary", "Summary."])

    assert result.exit_code == 1


def test_delete_with_yes_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "delete", "conventions", "--yes"])

    assert result.exit_code == 0
    assert not (tmp_path / ".sourcebook" / "lore" / "conventions.md").exists()


def test_delete_prompts_without_yes_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "delete", "conventions"], input="n\n")

    assert result.exit_code != 0
    assert (tmp_path / ".sourcebook" / "lore" / "conventions.md").exists()


def test_delete_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "delete", "missing", "--yes"])

    assert result.exit_code == 1


def test_assign_links_lore_to_world(tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "assign-world", "conventions"])

    assert result.exit_code == 0
    world_text = (tmp_path / ".sourcebook" / "world.md").read_text(encoding="utf-8")
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "conventions" in world_text
    assert "assigned_to_world: true" in lore_text


def test_assign_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["lore", "assign-world", "conventions"])

    assert result.exit_code == 1


def test_assign_missing_lore_fails() -> None:
    runner.invoke(app, ["bootstrap", "init"])

    result = runner.invoke(app, ["lore", "assign-world", "missing"])

    assert result.exit_code == 1


def test_assign_without_world_fails() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "assign-world", "conventions"])

    assert result.exit_code == 1


def test_unassign_clears_link(tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["lore", "assign-world", "conventions"])

    result = runner.invoke(app, ["lore", "unassign-world", "conventions"])

    assert result.exit_code == 0
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "assigned_to_world: false" in lore_text


def test_unassign_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["lore", "assign-world", "conventions"])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["lore", "unassign-world", "conventions"])

    assert result.exit_code == 1


def test_assign_region_links_lore_to_region(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "assign-region", "conventions", "northlands"])

    assert result.exit_code == 0
    region_text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "conventions" in region_text
    assert "northlands" in lore_text


def test_assign_region_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["lore", "assign-region", "conventions", "northlands"])

    assert result.exit_code == 1


def test_assign_region_missing_lore_fails() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "assign-region", "missing", "northlands"])

    assert result.exit_code == 1


def test_assign_region_missing_region_fails() -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "assign-region", "conventions", "missing"])

    assert result.exit_code == 1


def test_unassign_region_clears_link(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["lore", "assign-region", "conventions", "northlands"])

    result = runner.invoke(app, ["lore", "unassign-region", "conventions", "northlands"])

    assert result.exit_code == 0
    region_text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "conventions" not in region_text
    assert "assigned_regions: []" in lore_text


def test_unassign_region_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["lore", "assign-region", "conventions", "northlands"])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["lore", "unassign-region", "conventions", "northlands"])

    assert result.exit_code == 1


def test_enable_sets_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["lore", "disable", "conventions"])

    result = runner.invoke(app, ["lore", "enable", "conventions"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "enabled: true" in text


def test_disable_sets_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["lore", "disable", "conventions"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "enabled: false" in text


def test_enable_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["lore", "enable", "conventions"])

    assert result.exit_code == 1


def test_disable_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "text", "--summary", "Summary."])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["lore", "disable", "conventions"])

    assert result.exit_code == 1


def test_enable_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "enable", "missing"])

    assert result.exit_code == 1


def test_disable_missing_lore_fails() -> None:
    result = runner.invoke(app, ["lore", "disable", "missing"])

    assert result.exit_code == 1


def test_get_truncates_body_over_budget(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner.invoke(app, ["lore", "create", "conventions", "--body", "x" * 200, "--summary", "Summary."])
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 50)

    result = runner.invoke(app, ["lore", "get", "conventions"])

    assert result.exit_code == 0
    assert "[TRUNCATED" in result.output
    assert str(tmp_path / ".sourcebook" / "lore" / "conventions.md") in result.output


def test_list_pages_under_budget_and_cursor_resumes(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["lore", "create", "alpha", "--body", "b", "--summary", "s"])
    runner.invoke(app, ["lore", "create", "beta", "--body", "b", "--summary", "s"])
    runner.invoke(app, ["lore", "create", "gamma", "--body", "b", "--summary", "s"])
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 10)

    first = runner.invoke(app, ["lore", "list"])

    assert first.exit_code == 0
    assert "alpha" in first.output
    assert "beta" not in first.output
    assert "More results - pass --cursor 1 to continue." in first.output

    second = runner.invoke(app, ["lore", "list", "--cursor", "1"])

    assert second.exit_code == 0
    assert "beta" in second.output


def test_list_rejects_invalid_cursor() -> None:
    runner.invoke(app, ["lore", "create", "alpha", "--body", "b", "--summary", "s"])

    result = runner.invoke(app, ["lore", "list", "--cursor", "not-a-number"])

    assert result.exit_code == 1
