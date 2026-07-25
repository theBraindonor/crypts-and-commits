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
    runner.invoke(
        app,
        ["region", "create", "northlands", "--path", "src/frontend", "--body", "Body text.", "--summary", "Summary."],
    )

    result = runner.invoke(app, ["region", "get", "northlands"])

    assert result.exit_code == 0
    assert "name" in result.output
    assert "src/frontend" in result.output
    assert "Body text." in result.output


def test_get_preserves_bracketed_body_text() -> None:
    runner.invoke(
        app,
        ["region", "create", "northlands", "--body", "See [tool.pdm.workspace] for details.", "--summary", "Summary."],
    )

    result = runner.invoke(app, ["region", "get", "northlands"])

    assert result.exit_code == 0
    assert "[tool.pdm.workspace]" in result.output


def test_get_shows_placeholder_when_summary_absent(tmp_path: Path) -> None:
    # Summary is mandatory on create, so a summary-less entry can only exist as a
    # legacy/hand-written file; seed one directly to exercise the placeholder path.
    region_dir = tmp_path / ".sourcebook" / "region"
    region_dir.mkdir(parents=True)
    (region_dir / "northlands.md").write_text("---\nname: northlands\npath: ''\n---\n\nBody text.\n", encoding="utf-8")

    result = runner.invoke(app, ["region", "get", "northlands"])

    assert result.exit_code == 0
    assert "No summary has been set" in result.output


def test_get_truncates_body_over_budget(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "x" * 200, "--summary", "Summary."])
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 50)

    result = runner.invoke(app, ["region", "get", "northlands"])

    assert result.exit_code == 0
    assert "[TRUNCATED" in result.output
    assert str(tmp_path / ".sourcebook" / "region" / "northlands.md") in result.output


def test_list_pages_under_budget_and_cursor_resumes(monkeypatch: pytest.MonkeyPatch) -> None:
    runner.invoke(app, ["region", "create", "alpha", "--body", "b", "--summary", "s"])
    runner.invoke(app, ["region", "create", "beta", "--body", "b", "--summary", "s"])
    runner.invoke(app, ["region", "create", "gamma", "--body", "b", "--summary", "s"])
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 10)

    first = runner.invoke(app, ["region", "list"])

    assert first.exit_code == 0
    assert "alpha" in first.output
    assert "beta" not in first.output
    assert "More results - pass --cursor 1 to continue." in first.output

    second = runner.invoke(app, ["region", "list", "--cursor", "1"])

    assert second.exit_code == 0
    assert "beta" in second.output


def test_list_rejects_invalid_cursor() -> None:
    runner.invoke(app, ["region", "create", "alpha", "--body", "b", "--summary", "s"])

    result = runner.invoke(app, ["region", "list", "--cursor", "not-a-number"])

    assert result.exit_code == 1


def test_create_stores_summary_shown_in_get() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "Body text.", "--summary", "A routing signal."])

    result = runner.invoke(app, ["region", "get", "northlands"])

    assert result.exit_code == 0
    assert "A routing signal." in result.output


def test_set_summary_then_get_shows_it() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "Body text.", "--summary", "Summary."])

    set_result = runner.invoke(app, ["region", "set-summary", "northlands", "A brief routing signal."])
    get_result = runner.invoke(app, ["region", "get", "northlands"])

    assert set_result.exit_code == 0
    assert get_result.exit_code == 0
    assert "A brief routing signal." in get_result.output


def test_get_preserves_bracketed_summary_text() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "Body text.", "--summary", "Summary."])
    runner.invoke(app, ["region", "set-summary", "northlands", "Covers [tool.pdm.workspace] config."])

    result = runner.invoke(app, ["region", "get", "northlands"])

    assert result.exit_code == 0
    assert "[tool.pdm.workspace]" in result.output


def test_set_summary_rejects_value_over_cap() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["region", "set-summary", "northlands", "x" * 501])

    assert result.exit_code == 1
    assert "maximum of 500" in result.output


def test_set_summary_missing_region_fails() -> None:
    result = runner.invoke(app, ["region", "set-summary", "missing", "text"])

    assert result.exit_code == 1


def test_list_reports_no_region_files() -> None:
    result = runner.invoke(app, ["region", "list"])

    assert result.exit_code == 0
    assert "No region files found." in result.output


def test_create_with_body_option(tmp_path: Path) -> None:
    result = runner.invoke(app, ["region", "create", "northlands", "--body", "# Northlands", "--summary", "Summary."])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook" / "region" / "northlands.md").exists()


def test_create_requires_summary(tmp_path: Path) -> None:
    result = runner.invoke(app, ["region", "create", "northlands", "--body", "text"])

    assert result.exit_code == 1
    assert "summary is required" in result.output
    assert not (tmp_path / ".sourcebook" / "region" / "northlands.md").exists()


def test_create_rejects_over_cap_summary(tmp_path: Path) -> None:
    result = runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "x" * 501])

    assert result.exit_code == 1
    assert "maximum of 500" in result.output
    assert not (tmp_path / ".sourcebook" / "region" / "northlands.md").exists()


def test_create_rejects_invalid_name() -> None:
    result = runner.invoke(app, ["region", "create", "bad name", "--body", "text", "--summary", "Summary."])

    assert result.exit_code == 1
    assert "invalid" in result.output


def test_create_opens_editor_when_body_omitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli_common.click, "edit", lambda *_args, **_kwargs: "# Edited body")

    result = runner.invoke(app, ["region", "create", "northlands", "--summary", "Summary."])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "Edited body" in text


def test_list_shows_created_region() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["region", "list"])

    assert "northlands" in result.output


def test_update_replaces_body(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "Original", "--summary", "Summary."])

    result = runner.invoke(app, ["region", "update", "northlands", "--body", "Updated", "--summary", "Summary."])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "Updated" in text
    assert "Original" not in text


def test_update_regenerates_summary() -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "Original", "--summary", "Old summary."])

    update_result = runner.invoke(
        app, ["region", "update", "northlands", "--body", "Updated", "--summary", "New summary."]
    )
    get_result = runner.invoke(app, ["region", "get", "northlands"])

    assert update_result.exit_code == 0
    assert "New summary." in get_result.output
    assert "Updated" in get_result.output


def test_update_requires_summary(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "Original", "--summary", "Summary."])

    result = runner.invoke(app, ["region", "update", "northlands", "--body", "Updated"])

    assert result.exit_code == 1
    assert "summary is required" in result.output
    # The rejected update must not have touched the stored body.
    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "Original" in text
    assert "Updated" not in text


def test_update_missing_region_fails() -> None:
    result = runner.invoke(app, ["region", "update", "missing", "--body", "text", "--summary", "Summary."])

    assert result.exit_code == 1


def test_delete_with_yes_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["region", "delete", "northlands", "--yes"])

    assert result.exit_code == 0
    assert not (tmp_path / ".sourcebook" / "region" / "northlands.md").exists()


def test_delete_prompts_without_yes_flag(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["region", "delete", "northlands"], input="n\n")

    assert result.exit_code != 0
    assert (tmp_path / ".sourcebook" / "region" / "northlands.md").exists()


def test_delete_missing_region_fails() -> None:
    result = runner.invoke(app, ["region", "delete", "missing"])

    assert result.exit_code == 1


def test_create_with_path_option(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["region", "create", "frontend", "--path", "src/frontend", "--body", "text", "--summary", "Summary."]
    )

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "region" / "frontend.md").read_text(encoding="utf-8")
    assert "path: src/frontend" in text


def test_set_path_updates_path(tmp_path: Path) -> None:
    runner.invoke(app, ["region", "create", "northlands", "--body", "text", "--summary", "Summary."])

    result = runner.invoke(app, ["region", "set-path", "northlands", "src/backend"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "path: src/backend" in text


def test_set_path_missing_region_fails() -> None:
    result = runner.invoke(app, ["region", "set-path", "missing", "src/backend"])

    assert result.exit_code == 1
