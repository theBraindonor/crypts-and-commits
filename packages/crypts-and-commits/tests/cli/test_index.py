from pathlib import Path

import pytest
from cac.cli.app import app
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_status_before_rebuild_reports_no_index() -> None:
    result = runner.invoke(app, ["index", "status"])

    assert result.exit_code == 0
    assert "No index has been built yet" in result.output


def test_rebuild_reports_indexed_count() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "-c", "opening-gambit", "--body", "Fight goblins."])

    result = runner.invoke(app, ["index", "rebuild"])

    assert result.exit_code == 0
    assert "1" in result.output


def test_status_after_rebuild_reports_counts_by_type() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "-c", "opening-gambit", "--body", "Fight goblins."])
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "status"])

    assert result.exit_code == 0
    assert "1 item(s) indexed" in result.output
    assert "encounter: 1" in result.output


def test_search_before_rebuild_reports_no_index() -> None:
    result = runner.invoke(app, ["index", "search", "goblins"])

    assert result.exit_code == 0
    assert "No index has been built yet" in result.output


def test_search_finds_matching_encounter() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "-c", "opening-gambit", "--body", "Fight goblins."])
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "search", "goblins"])

    assert result.exit_code == 0
    assert "#1" in result.output
    assert "goblin-ambush" in result.output
    assert "draft" in result.output


def test_search_no_match_reports_no_results() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "-c", "opening-gambit", "--body", "Fight goblins."])
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "search", "dragons"])

    assert result.exit_code == 0
    assert "No results" in result.output


def test_search_max_results_and_skip_narrow_the_page() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    for i in range(3):
        runner.invoke(
            app, ["encounter", "create", f"goblin-ambush-{i}", "-c", "opening-gambit", "--body", "Fight goblins."]
        )
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "search", "goblins", "--max-results", "1", "--skip", "1"])

    assert result.exit_code == 0
    assert "#2" in result.output


def test_search_invalid_type_exits_nonzero() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "-c", "opening-gambit", "--body", "Fight goblins."])
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "search", "goblins", "--type", "bogus"])

    assert result.exit_code != 0
    assert "Unknown document type" in result.output
