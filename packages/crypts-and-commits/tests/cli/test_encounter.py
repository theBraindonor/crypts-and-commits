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


def _create_campaign(name: str = "opening-gambit") -> None:
    runner.invoke(app, ["campaign", "create", name, "--body", "text"])


def _open_campaign(name: str = "opening-gambit") -> None:
    runner.invoke(app, ["campaign", "open", name])


def test_get_missing_encounter_fails() -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "get", "missing", "--campaign", "opening-gambit"])

    assert result.exit_code == 1


def test_get_shows_metadata_and_body() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "Body text."])

    result = runner.invoke(app, ["encounter", "get", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code == 0
    assert "name" in result.output
    assert "status" in result.output
    assert "Body text." in result.output


def test_get_preserves_bracketed_body_text() -> None:
    _create_campaign()
    runner.invoke(
        app,
        ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "See [tool.pdm.workspace]."],
    )

    result = runner.invoke(app, ["encounter", "get", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code == 0
    assert "[tool.pdm.workspace]" in result.output


def test_list_reports_no_encounter_files() -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "list", "--campaign", "opening-gambit"])

    assert result.exit_code == 0
    assert "No encounter files found." in result.output


def test_create_requires_existing_campaign() -> None:
    result = runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "missing", "--body", "text"])

    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_create_with_body_option(tmp_path: Path) -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "-b", "# Go"])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").exists()


def test_create_rejects_invalid_name() -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "create", "bad name", "--campaign", "opening-gambit", "--body", "text"])

    assert result.exit_code == 1
    assert "invalid" in result.output


def test_create_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    _create_campaign()
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "-b", "text"])

    assert result.exit_code == 1
    assert "git user.name is not configured" in result.output


def test_review_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])

    assert result.exit_code == 1
    assert "git user.name is not configured" in result.output


def test_create_opens_editor_when_body_omitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _create_campaign()
    monkeypatch.setattr(cli_common.click, "edit", lambda *_args, **_kwargs: "## Requirements\n\nEdited body")

    result = runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "Edited body" in text


def test_list_shows_created_encounter() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["encounter", "list", "--campaign", "opening-gambit"])

    assert "goblin-ambush" in result.output


def test_update_replaces_body(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "Original"])

    result = runner.invoke(
        app, ["encounter", "update", "goblin-ambush", "--campaign", "opening-gambit", "--body", "Updated"]
    )

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "Updated" in text
    assert "Original" not in text


def test_update_missing_encounter_fails() -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "update", "missing", "--campaign", "opening-gambit", "--body", "text"])

    assert result.exit_code == 1


def test_update_rejects_once_not_draft(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "Original"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "--message", "Lore."])

    result = runner.invoke(
        app, ["encounter", "update", "goblin-ambush", "--campaign", "opening-gambit", "--body", "Updated"]
    )

    assert result.exit_code == 1
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "Original" in text
    assert "Updated" not in text


def test_delete_with_yes_flag(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["encounter", "delete", "goblin-ambush", "--campaign", "opening-gambit", "--yes"])

    assert result.exit_code == 0
    assert not (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").exists()


def test_delete_missing_encounter_fails() -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "delete", "missing", "--campaign", "opening-gambit", "--yes"])

    assert result.exit_code == 1


def test_set_status_command_removed() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["encounter", "set-status", "goblin-ambush", "abandoned"])

    assert result.exit_code != 0


def test_review_appends_message_and_updates_status(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "status: reviewed" in text
    assert "Lore." in text


def test_review_requires_message() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code != 0


def test_review_rejects_wrong_status() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "First."])

    result = runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Two."])

    assert result.exit_code == 1


def test_open_without_message_succeeds(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])

    result = runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "status: open" in text


def test_open_with_message_appends_entry(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])

    result = runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Go."])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "Go." in text


def test_open_rejects_from_draft() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code == 1


def test_record_message_succeeds_when_reviewed(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])

    result = runner.invoke(
        app, ["encounter", "record-message", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Noted."]
    )

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "Noted." in text


def test_record_message_succeeds_when_open(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])
    runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])

    result = runner.invoke(
        app, ["encounter", "record-message", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Noted."]
    )

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "Noted." in text


def test_record_message_rejects_when_draft() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(
        app, ["encounter", "record-message", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Noted."]
    )

    assert result.exit_code == 1


def test_record_message_requires_message() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])

    result = runner.invoke(app, ["encounter", "record-message", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code != 0


def test_complete_without_message_succeeds(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])
    runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])

    result = runner.invoke(app, ["encounter", "complete", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "status: completed" in text


def test_complete_with_message_appends_entry(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])
    runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])

    result = runner.invoke(
        app, ["encounter", "complete", "goblin-ambush", "--campaign", "opening-gambit", "-m", "All verified."]
    )

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "All verified." in text


def test_complete_rejects_from_reviewed() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])

    result = runner.invoke(app, ["encounter", "complete", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code == 1


def test_abandon_from_open_succeeds(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])
    runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])

    result = runner.invoke(
        app, ["encounter", "abandon", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Cancelled."]
    )

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "status: abandoned" in text


def test_abandon_rejects_from_completed() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Lore."])
    runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])
    runner.invoke(app, ["encounter", "complete", "goblin-ambush", "--campaign", "opening-gambit"])

    result = runner.invoke(
        app, ["encounter", "abandon", "goblin-ambush", "--campaign", "opening-gambit", "-m", "Too late."]
    )

    assert result.exit_code == 1


def test_abandon_requires_message() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["encounter", "abandon", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code != 0


def test_assign_region_sets_region(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(
        app, ["encounter", "assign-region", "goblin-ambush", "northlands", "--campaign", "opening-gambit"]
    )

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "regions:" in text
    assert "northlands" in text
    region_text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "goblin-ambush" not in region_text


def test_assign_region_allows_multiple_regions(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["region", "create", "southlands", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    runner.invoke(app, ["encounter", "assign-region", "goblin-ambush", "northlands", "--campaign", "opening-gambit"])
    result = runner.invoke(
        app, ["encounter", "assign-region", "goblin-ambush", "southlands", "--campaign", "opening-gambit"]
    )

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "northlands" in text
    assert "southlands" in text


def test_assign_region_missing_region_fails() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(
        app, ["encounter", "assign-region", "goblin-ambush", "missing", "--campaign", "opening-gambit"]
    )

    assert result.exit_code == 1


def test_assign_region_rejected_once_open() -> None:
    _create_campaign()
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "--message", "Lore."])
    runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])

    result = runner.invoke(
        app, ["encounter", "assign-region", "goblin-ambush", "northlands", "--campaign", "opening-gambit"]
    )

    assert result.exit_code == 1


def test_unassign_region_clears_region(tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "assign-region", "goblin-ambush", "northlands", "--campaign", "opening-gambit"])

    result = runner.invoke(
        app, ["encounter", "unassign-region", "goblin-ambush", "northlands", "--campaign", "opening-gambit"]
    )

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").read_text(encoding="utf-8")
    assert "regions: []" in text


# --- Campaign resolution (optional --campaign, defaulting to the active campaign) ---


def test_create_defaults_to_active_campaign(tmp_path: Path) -> None:
    _create_campaign("live")
    _open_campaign("live")

    result = runner.invoke(app, ["encounter", "create", "goblin-ambush", "--body", "text"])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook" / "encounters" / "live" / "goblin-ambush.md").exists()


def test_get_defaults_to_active_campaign() -> None:
    _create_campaign("live")
    _open_campaign("live")
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--body", "Body text."])

    result = runner.invoke(app, ["encounter", "get", "goblin-ambush"])

    assert result.exit_code == 0
    assert "Body text." in result.output


def test_list_defaults_to_active_campaign() -> None:
    _create_campaign("live")
    _open_campaign("live")
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--body", "text"])

    result = runner.invoke(app, ["encounter", "list"])

    assert result.exit_code == 0
    assert "goblin-ambush" in result.output


def test_create_without_campaign_and_none_active_fails() -> None:
    _create_campaign()  # draft, never opened -> no active campaign

    result = runner.invoke(app, ["encounter", "create", "goblin-ambush", "--body", "text"])

    assert result.exit_code == 1
    assert "No campaign is currently open" in result.output


def test_list_without_campaign_and_none_active_fails() -> None:
    _create_campaign()

    result = runner.invoke(app, ["encounter", "list"])

    assert result.exit_code == 1
    assert "No campaign is currently open" in result.output


@pytest.mark.parametrize("terminal_action", ["complete", "abandon"])
def test_create_rejects_terminal_campaign(terminal_action: str) -> None:
    _create_campaign("closed")
    _open_campaign("closed")
    runner.invoke(app, ["campaign", terminal_action, "closed", "--message", "Postmortem."])

    result = runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "closed", "--body", "text"])

    assert result.exit_code == 1
    assert "no longer be created or modified" in " ".join(result.output.split())


def test_get_allows_terminal_campaign() -> None:
    _create_campaign("closed")
    _open_campaign("closed")
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "closed", "--body", "Body text."])
    runner.invoke(app, ["campaign", "complete", "closed", "--message", "Postmortem."])

    result = runner.invoke(app, ["encounter", "get", "goblin-ambush", "--campaign", "closed"])

    assert result.exit_code == 0
    assert "Body text." in result.output


def test_list_allows_terminal_campaign() -> None:
    _create_campaign("closed")
    _open_campaign("closed")
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "closed", "--body", "text"])
    runner.invoke(app, ["campaign", "abandon", "closed", "--message", "Postmortem."])

    result = runner.invoke(app, ["encounter", "list", "--campaign", "closed"])

    assert result.exit_code == 0
    assert "goblin-ambush" in result.output


def test_get_truncates_body_over_budget(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "x" * 200])
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 50)

    result = runner.invoke(app, ["encounter", "get", "goblin-ambush", "--campaign", "opening-gambit"])

    assert result.exit_code == 0
    assert "[TRUNCATED" in result.output
    expected_path = tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md"
    assert str(expected_path) in result.output


def test_list_rejects_invalid_cursor() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["encounter", "list", "--campaign", "opening-gambit", "--cursor", "not-a-number"])

    assert result.exit_code == 1


def test_assign_and_unassign_dependency_commands() -> None:
    _create_campaign()
    for name in ("foundation", "feature"):
        runner.invoke(app, ["encounter", "create", name, "--campaign", "opening-gambit", "--body", "text"])

    assigned = runner.invoke(
        app, ["encounter", "assign-dependency", "feature", "foundation", "--campaign", "opening-gambit"]
    )
    get_assigned = runner.invoke(app, ["encounter", "get", "feature", "--campaign", "opening-gambit"])
    unassigned = runner.invoke(
        app, ["encounter", "unassign-dependency", "feature", "foundation", "--campaign", "opening-gambit"]
    )
    get_unassigned = runner.invoke(app, ["encounter", "get", "feature", "--campaign", "opening-gambit"])

    assert assigned.exit_code == 0
    assert "foundation" in get_assigned.output
    assert unassigned.exit_code == 0
    assert "depends_on: []" in get_unassigned.output


def test_assign_dependency_reports_validation_failure() -> None:
    _create_campaign()
    runner.invoke(app, ["encounter", "create", "feature", "--campaign", "opening-gambit", "--body", "text"])

    result = runner.invoke(
        app, ["encounter", "assign-dependency", "feature", "missing", "--campaign", "opening-gambit"]
    )

    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_dependency_commands_default_to_active_campaign() -> None:
    _create_campaign("live")
    _open_campaign("live")
    for name in ("foundation", "feature"):
        runner.invoke(app, ["encounter", "create", name, "--body", "text"])

    result = runner.invoke(app, ["encounter", "assign-dependency", "feature", "foundation"])

    assert result.exit_code == 0
    assert "foundation" in runner.invoke(app, ["encounter", "get", "feature"]).output


def test_order_prints_status_and_dependencies_without_stripping_brackets() -> None:
    _create_campaign()
    for name in ("foundation", "feature"):
        runner.invoke(app, ["encounter", "create", name, "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "assign-dependency", "feature", "foundation", "--campaign", "opening-gambit"])

    result = runner.invoke(app, ["encounter", "order", "--campaign", "opening-gambit"])

    assert result.exit_code == 0
    assert result.output.splitlines() == [
        "foundation [draft] depends_on: (none)",
        "feature [draft] depends_on: foundation",
    ]


def test_order_defaults_to_active_campaign_and_allows_terminal_campaign() -> None:
    _create_campaign("live")
    _open_campaign("live")
    runner.invoke(app, ["encounter", "create", "feature", "--body", "text"])

    active_result = runner.invoke(app, ["encounter", "order"])
    runner.invoke(app, ["campaign", "complete", "live", "--message", "Postmortem."])
    terminal_result = runner.invoke(app, ["encounter", "order", "--campaign", "live"])

    assert active_result.exit_code == 0
    assert "feature [draft]" in active_result.output
    assert terminal_result.exit_code == 0
    assert "feature [draft]" in terminal_result.output


def test_open_reports_all_incomplete_dependency_statuses() -> None:
    _create_campaign()
    for name in ("foundation", "feature"):
        runner.invoke(app, ["encounter", "create", name, "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "assign-dependency", "feature", "foundation", "--campaign", "opening-gambit"])
    runner.invoke(app, ["encounter", "review", "feature", "--campaign", "opening-gambit", "--message", "Reviewed."])

    result = runner.invoke(app, ["encounter", "open", "feature", "--campaign", "opening-gambit"])

    assert result.exit_code == 1
    assert "foundation (draft)" in result.output


def test_delete_reports_dependent_encounters() -> None:
    _create_campaign()
    for name in ("foundation", "feature"):
        runner.invoke(app, ["encounter", "create", name, "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["encounter", "assign-dependency", "feature", "foundation", "--campaign", "opening-gambit"])

    result = runner.invoke(app, ["encounter", "delete", "foundation", "--campaign", "opening-gambit", "--yes"])

    assert result.exit_code == 1
    assert "required by: feature" in result.output
