import json

import pytest
from cac.cli.app import app
from cac.core import boss, boss_candidates, config, world
from cac.mcp.boss import boss_candidates as api_candidates
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture(autouse=True)
def bootstrapped(tmp_path):
    world.initialize_world(tmp_path)


def invoke(*args):
    return runner.invoke(app, ["boss", "candidates", *args])


def test_cli_and_mcp_agree_and_print_literal_markdown(tmp_path):
    boss.create_boss(tmp_path, "goal", "Secret body", "[bold]literal[/bold] [tool.ruff]")
    boss.make_available(tmp_path, "goal")
    result = invoke()
    assert result.exit_code == 0, result.output
    assert "[bold]literal[/bold] [tool.ruff]" in result.output
    assert "Secret body" not in result.output
    assert json.loads(result.output) == api_candidates() == boss_candidates.candidates(tmp_path)
    assert json.loads(result.output)["counts"]["eligible"] == 1


def test_candidate_command_help_and_invalid_cursor():
    help_result = invoke("--help")
    assert help_result.exit_code == 0
    assert "--cursor" in help_result.output
    invalid = invoke("--cursor", "bad")
    assert invalid.exit_code == 1
    assert "Cursor" in invalid.output


def test_cli_paging_and_collection_diagnostics(tmp_path, monkeypatch):
    for name in ("b002-goal", "b010-goal", "legacy"):
        boss.create_boss(tmp_path, name, "Body", "Summary")
        boss.make_available(tmp_path, name)
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 1250)
    cursor, seen = None, []
    while True:
        result = invoke(*(["--cursor", cursor] if cursor else []))
        assert result.exit_code == 0, result.output
        page = json.loads(result.output)
        assert page == api_candidates(cursor)
        assert len(result.output.rstrip()) <= 1250
        seen.extend(entry["name"] for entry in page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert seen == ["b002-goal", "b010-goal", "legacy"]


def test_cli_reports_storage_error_without_traceback(tmp_path):
    directory = boss.boss_dir(tmp_path)
    directory.write_text("[stored] collision", encoding="utf-8")
    result = invoke()
    assert result.exit_code == 1
    assert "collision" in result.output
    assert "Traceback" not in result.output
