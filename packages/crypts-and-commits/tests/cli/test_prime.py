from pathlib import Path

import pytest
from typer.testing import CliRunner

from cac.cli.app import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def _bootstrap() -> None:
    runner.invoke(app, ["bootstrap", "init"])


def test_get_fails_without_bootstrap() -> None:
    result = runner.invoke(app, ["prime", "get"])

    assert result.exit_code == 1


def test_get_shows_world_and_no_campaign_message() -> None:
    _bootstrap()

    result = runner.invoke(app, ["prime", "get"])

    assert result.exit_code == 0
    assert "Unnamed World" in result.output
    assert "No campaign is currently open." in result.output


def test_get_shows_enabled_world_lore_summary() -> None:
    _bootstrap()
    runner.invoke(app, ["lore", "create", "world-lore", "--body", "Body.", "--summary", "World lore summary."])
    runner.invoke(app, ["lore", "assign-world", "world-lore"])

    result = runner.invoke(app, ["prime", "get"])

    assert result.exit_code == 0
    assert "world-lore" in result.output
    assert "World lore summary." in result.output


def test_get_excludes_disabled_world_lore_summary() -> None:
    _bootstrap()
    runner.invoke(app, ["lore", "create", "world-lore", "--body", "Body.", "--summary", "World lore summary."])
    runner.invoke(app, ["lore", "assign-world", "world-lore"])
    runner.invoke(app, ["lore", "disable", "world-lore"])

    result = runner.invoke(app, ["prime", "get"])

    assert result.exit_code == 0
    assert "No enabled lore is assigned to the world." in result.output


def test_get_shows_region_map_with_edges_only() -> None:
    _bootstrap()
    runner.invoke(
        app,
        ["region", "create", "northlands", "--path", "src/north", "--body", "Body.", "--summary", "Region summary."],
    )
    runner.invoke(app, ["lore", "create", "region-lore", "--body", "Body.", "--summary", "Region lore summary."])
    runner.invoke(app, ["lore", "assign-region", "region-lore", "northlands"])

    result = runner.invoke(app, ["prime", "get"])

    assert result.exit_code == 0
    assert "northlands" in result.output
    assert "src/north" in result.output
    assert "Region summary." in result.output
    assert "region-lore" in result.output
    # Edges only: the region-scoped lore's own summary text does not belong at global scope.
    assert "Region lore summary." not in result.output


def test_get_preserves_bracketed_body_text() -> None:
    _bootstrap()
    runner.invoke(app, ["world", "set-body", "--body", "See [tool.pdm.workspace] for details."])

    result = runner.invoke(app, ["prime", "get"])

    assert result.exit_code == 0
    assert "[tool.pdm.workspace]" in result.output


def test_get_shows_active_campaign_body_not_encounters() -> None:
    _bootstrap()
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Campaign body."])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--body", "Encounter body."])

    result = runner.invoke(app, ["prime", "get"])

    assert result.exit_code == 0
    assert "opening-gambit" in result.output
    assert "Campaign body." in result.output
    assert "goblin-ambush" not in result.output


def test_applicable_lore_missing_encounter_fails() -> None:
    _bootstrap()
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])

    result = runner.invoke(app, ["prime", "applicable-lore", "missing"])

    assert result.exit_code == 1


def test_applicable_lore_no_active_campaign_fails() -> None:
    _bootstrap()

    result = runner.invoke(app, ["prime", "applicable-lore", "goblin-ambush"])

    assert result.exit_code == 1


def test_applicable_lore_shows_world_and_region_lore() -> None:
    _bootstrap()
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--body", "Body."])
    runner.invoke(app, ["region", "create", "northlands", "--body", "Body.", "--summary", "Region summary."])
    runner.invoke(app, ["encounter", "assign-region", "goblin-ambush", "northlands"])
    runner.invoke(app, ["lore", "create", "world-lore", "--body", "Body.", "--summary", "World lore summary."])
    runner.invoke(app, ["lore", "assign-world", "world-lore"])
    runner.invoke(app, ["lore", "create", "region-lore", "--body", "Body.", "--summary", "Region lore summary."])
    runner.invoke(app, ["lore", "assign-region", "region-lore", "northlands"])

    result = runner.invoke(app, ["prime", "applicable-lore", "goblin-ambush"])

    assert result.exit_code == 0
    assert "world-lore" in result.output
    assert "World lore summary." in result.output
    assert "region-lore" in result.output
    assert "Region lore summary." in result.output


def test_applicable_lore_reports_when_none_found() -> None:
    _bootstrap()
    runner.invoke(app, ["campaign", "create", "opening-gambit", "--body", "Body."])
    runner.invoke(app, ["campaign", "open", "opening-gambit"])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--body", "Body."])

    result = runner.invoke(app, ["prime", "applicable-lore", "goblin-ambush"])

    assert result.exit_code == 0
    assert "No applicable enabled lore was found for this encounter." in result.output


def test_applicable_lore_accepts_explicit_campaign() -> None:
    _bootstrap()
    runner.invoke(app, ["campaign", "create", "side-quest", "--body", "Body."])
    runner.invoke(app, ["campaign", "open", "side-quest"])
    runner.invoke(app, ["encounter", "create", "goblin-ambush", "--body", "Body."])
    runner.invoke(app, ["campaign", "pause", "side-quest"])

    result = runner.invoke(app, ["prime", "applicable-lore", "goblin-ambush", "--campaign", "side-quest"])

    assert result.exit_code == 0
    assert "No applicable enabled lore was found for this encounter." in result.output
