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


def test_list_shows_campaign_status(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])

    result = runner.invoke(app, ["campaign", "list"])

    assert result.exit_code == 0
    assert "opening-gambit (open)" in result.output


def test_create_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    assert result.exit_code == 1


def test_update_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["campaign", "update", "opening-gambit", "--body", "Updated"])

    assert result.exit_code == 1


def test_open_updates_status(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["campaign", "open", "opening-gambit"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").read_text(encoding="utf-8")
    assert "status: open" in text


def test_open_missing_campaign_fails() -> None:
    result = runner.invoke(app, ["campaign", "open", "missing"])

    assert result.exit_code == 1


def test_open_rejects_invalid_transition() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["campaign", "complete", "opening-gambit", "--message", "Shipped."])

    result = runner.invoke(app, ["campaign", "open", "opening-gambit"])

    assert result.exit_code == 1


def test_open_fails_while_another_campaign_is_open() -> None:
    runner.invoke(app, ["campaign", "create", "first", "--body", "text"])
    runner.invoke(app, ["campaign", "create", "second", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "first"])

    result = runner.invoke(app, ["campaign", "open", "second"])

    assert result.exit_code == 1
    assert "first" in result.output


def test_open_fails_when_git_identity_unresolvable(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["campaign", "open", "opening-gambit"])

    assert result.exit_code == 1


def test_pause_updates_status(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])

    result = runner.invoke(app, ["campaign", "pause", "opening-gambit"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").read_text(encoding="utf-8")
    assert "status: paused" in text


def test_pause_rejects_invalid_transition_from_draft() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["campaign", "pause", "opening-gambit"])

    assert result.exit_code == 1


def test_pause_fails_with_open_encounter() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["region", "create", "default-region", "--body", "text", "--summary", "Summary."])
    runner.invoke(
        app, ["encounter", "assign-region", "goblin-ambush", "default-region", "--campaign", "opening-gambit"]
    )
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "--message", "ok"])
    runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])

    result = runner.invoke(app, ["campaign", "pause", "opening-gambit"])

    assert result.exit_code == 1
    assert "goblin-ambush" in result.output


def test_complete_updates_status(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])

    result = runner.invoke(app, ["campaign", "complete", "opening-gambit", "--message", "Shipped."])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").read_text(encoding="utf-8")
    assert "status: completed" in text


def test_complete_fails_with_open_encounter() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["region", "create", "default-region", "--body", "text", "--summary", "Summary."])
    runner.invoke(
        app, ["encounter", "assign-region", "goblin-ambush", "default-region", "--campaign", "opening-gambit"]
    )
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "--message", "ok"])
    runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])

    result = runner.invoke(app, ["campaign", "complete", "opening-gambit", "--message", "Shipped."])

    assert result.exit_code == 1
    assert "goblin-ambush" in result.output


def test_abandon_updates_status(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["campaign", "abandon", "opening-gambit", "--message", "Called off."])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").read_text(encoding="utf-8")
    assert "status: abandoned" in text


def test_abandon_rejects_invalid_transition_from_completed() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["campaign", "complete", "opening-gambit", "--message", "Shipped."])

    result = runner.invoke(app, ["campaign", "abandon", "opening-gambit", "--message", "Called off."])

    assert result.exit_code == 1


def test_abandon_fails_with_open_encounter() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["region", "create", "default-region", "--body", "text", "--summary", "Summary."])
    runner.invoke(
        app, ["encounter", "assign-region", "goblin-ambush", "default-region", "--campaign", "opening-gambit"]
    )
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "--message", "ok"])
    runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])

    result = runner.invoke(app, ["campaign", "abandon", "opening-gambit", "--message", "Called off."])

    assert result.exit_code == 1
    assert "goblin-ambush" in result.output


def test_abandon_missing_campaign_fails() -> None:
    result = runner.invoke(app, ["campaign", "abandon", "missing", "--message", "Called off."])

    assert result.exit_code == 1


def test_complete_requires_message() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])

    result = runner.invoke(app, ["campaign", "complete", "opening-gambit"])

    assert result.exit_code != 0


def test_complete_rejects_blank_message() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])

    result = runner.invoke(app, ["campaign", "complete", "opening-gambit", "--message", "   "])

    assert result.exit_code == 1


def test_abandon_requires_message() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["campaign", "abandon", "opening-gambit"])

    assert result.exit_code != 0


def test_complete_appends_postmortem_to_body(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])

    runner.invoke(app, ["campaign", "complete", "opening-gambit", "--message", "Shipped the MVP."])

    text = (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").read_text(encoding="utf-8")
    assert "## Log" in text
    assert "Shipped the MVP." in text


def test_abandon_appends_postmortem_to_body(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    runner.invoke(app, ["campaign", "abandon", "opening-gambit", "--message", "Scope changed."])

    text = (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").read_text(encoding="utf-8")
    assert "## Log" in text
    assert "Scope changed." in text


@pytest.mark.parametrize("terminal_command", [["complete"], ["abandon"]])
def test_update_fails_once_campaign_is_terminal(tmp_path: Path, terminal_command: list[str]) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Original"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["campaign", *terminal_command, "opening-gambit", "--message", "Done."])

    result = runner.invoke(app, ["campaign", "update", "opening-gambit", "--body", "Rewritten"])

    assert result.exit_code == 1
    text = (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").read_text(encoding="utf-8")
    assert "Rewritten" not in text


def test_get_truncates_body_over_budget(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "x" * 200])
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 50)

    result = runner.invoke(app, ["campaign", "get", "opening-gambit"])

    assert result.exit_code == 0
    assert "[TRUNCATED" in result.output
    assert str(tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md") in result.output


def test_list_pages_under_budget_and_cursor_resumes(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["campaign", "create", "alpha", "--body", "b"])
    runner.invoke(app, ["campaign", "create", "beta", "--body", "b"])
    runner.invoke(app, ["campaign", "create", "gamma", "--body", "b"])
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 20)

    first = runner.invoke(app, ["campaign", "list"])

    assert first.exit_code == 0
    assert "alpha (draft)" in first.output
    assert "beta (draft)" not in first.output
    assert "More results - pass --cursor 1 to continue." in first.output

    second = runner.invoke(app, ["campaign", "list", "--cursor", "1"])

    assert second.exit_code == 0
    assert "beta (draft)" in second.output


def test_list_rejects_invalid_cursor() -> None:
    runner.invoke(app, ["campaign", "create", "alpha", "--body", "b"])

    result = runner.invoke(app, ["campaign", "list", "--cursor", "not-a-number"])

    assert result.exit_code == 1


def _complete_campaign_with_encounter(tmp_path: Path) -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["region", "create", "default-region", "--body", "text", "--summary", "Summary."])
    runner.invoke(
        app, ["encounter", "assign-region", "goblin-ambush", "default-region", "--campaign", "opening-gambit"]
    )
    runner.invoke(app, ["encounter", "review", "goblin-ambush", "--campaign", "opening-gambit", "--message", "ok"])
    runner.invoke(app, ["encounter", "open", "goblin-ambush", "--campaign", "opening-gambit"])
    runner.invoke(app, ["encounter", "complete", "goblin-ambush", "--campaign", "opening-gambit"])
    runner.invoke(app, ["campaign", "complete", "opening-gambit", "--message", "Shipped."])


def test_archive_moves_campaign_and_encounter(tmp_path: Path) -> None:
    _complete_campaign_with_encounter(tmp_path)

    result = runner.invoke(app, ["campaign", "archive", "opening-gambit"])

    assert result.exit_code == 0
    assert "1 encounter(s)" in result.output
    assert not (tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md").exists()
    assert not (tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md").exists()
    assert (tmp_path / ".sourcebook" / "archive" / "campaigns" / "opening-gambit.md").exists()
    assert (tmp_path / ".sourcebook" / "archive" / "encounters" / "opening-gambit" / "goblin-ambush.md").exists()


def test_archive_missing_campaign_fails() -> None:
    result = runner.invoke(app, ["campaign", "archive", "missing"])

    assert result.exit_code == 1


def test_archive_rejects_non_terminal_campaign() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])

    result = runner.invoke(app, ["campaign", "archive", "opening-gambit"])

    assert result.exit_code == 1


def test_archive_rejects_unfinished_encounter() -> None:
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["encounter", "create", "dragon-hoard", "--campaign", "opening-gambit", "--body", "text"])
    runner.invoke(app, ["campaign", "complete", "opening-gambit", "--message", "Shipped."])

    result = runner.invoke(app, ["campaign", "archive", "opening-gambit"])

    assert result.exit_code == 1
    assert "dragon-hoard" in result.output


def test_archive_rejects_already_archived(tmp_path: Path) -> None:
    _complete_campaign_with_encounter(tmp_path)
    runner.invoke(app, ["campaign", "archive", "opening-gambit"])

    result = runner.invoke(app, ["campaign", "archive", "opening-gambit"])

    assert result.exit_code == 1


def test_get_and_list_after_archiving(tmp_path: Path) -> None:
    _complete_campaign_with_encounter(tmp_path)
    runner.invoke(app, ["campaign", "archive", "opening-gambit"])

    get_result = runner.invoke(app, ["campaign", "get", "opening-gambit"])
    list_result = runner.invoke(app, ["campaign", "list"])

    assert get_result.exit_code == 0
    assert "text" in get_result.output
    assert "opening-gambit" not in list_result.output
