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
    assert "3" in result.output


def test_status_after_rebuild_reports_counts_by_type() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "-c", "opening-gambit", "--body", "Fight goblins."])
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "status"])

    assert result.exit_code == 0
    assert "3 item(s) indexed" in result.output
    assert "encounter: 1" in result.output
    assert "world: 1" in result.output
    assert "campaign: 1" in result.output


def test_search_finds_matching_lore() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["lore", "create", "clean-code", "--body", "Keep functions short.", "--summary", "Summary."])
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "search", "functions", "--type", "lore"])

    assert result.exit_code == 0
    assert "[lore]" in result.output
    assert "clean-code" in result.output
    assert "enabled" in result.output


def test_search_finds_matching_region() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["region", "create", "backend", "--body", "FastAPI service internals.", "--summary", "Summary."])
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "search", "FastAPI", "--type", "region"])

    assert result.exit_code == 0
    assert "[region]" in result.output
    assert "backend" in result.output


def test_search_finds_matching_campaign() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Recover the distinctive-campaign-hoard."])
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "search", "distinctive-campaign-hoard", "--type", "campaign"])

    assert result.exit_code == 0
    assert "[campaign]" in result.output
    assert "opening-gambit" in result.output


def test_search_finds_matching_world() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["world", "set-body", "--body", "This world is about distinctive-world-phrase content."])
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "search", "distinctive-world-phrase", "--type", "world"])

    assert result.exit_code == 0
    assert "[world]" in result.output


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
    assert "RANK  SCORE   TYPE        NAME  STATUS  UPDATED" in result.output
    assert "#1" in result.output
    assert "[encounter]" in result.output
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


def test_search_snippet_tokens_narrows_excerpt() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    body = "goblins " + " ".join(f"word{i}" for i in range(40))
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "-c", "opening-gambit", "--body", body])
    runner.invoke(app, ["index", "rebuild"])

    short_result = runner.invoke(app, ["index", "search", "goblins", "--snippet-tokens", "1"])
    long_result = runner.invoke(app, ["index", "search", "goblins", "--snippet-tokens", "64"])

    assert short_result.exit_code == 0
    assert long_result.exit_code == 0
    assert "word39" not in short_result.output
    assert "word39" in long_result.output


def test_search_invalid_snippet_tokens_exits_nonzero() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "-c", "opening-gambit", "--body", "Fight goblins."])
    runner.invoke(app, ["index", "rebuild"])

    result = runner.invoke(app, ["index", "search", "goblins", "--snippet-tokens", "65"])

    assert result.exit_code != 0
    assert "snippet_tokens" in result.output


def test_search_excludes_archived_campaign_by_default_and_includes_with_flag() -> None:
    runner.invoke(app, ["bootstrap", "init"])
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Recover the goblin hoard."])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["campaign", "complete", "opening-gambit", "--message", "Shipped."])
    runner.invoke(app, ["campaign", "archive", "opening-gambit"])
    runner.invoke(app, ["index", "rebuild"])

    default_result = runner.invoke(app, ["index", "search", "goblin", "--type", "campaign"])
    included_result = runner.invoke(app, ["index", "search", "goblin", "--type", "campaign", "--include-archived"])

    assert default_result.exit_code == 0
    assert "No results" in default_result.output
    assert included_result.exit_code == 0
    assert "opening-gambit" in included_result.output
    assert "(archived)" in included_result.output
