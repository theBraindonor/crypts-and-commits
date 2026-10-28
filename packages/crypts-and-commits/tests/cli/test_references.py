import pytest
from cac.cli.app import app
from cac.core import boss, campaign, config, encounter, references, region, world
from cac.mcp import encounter as api
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture(autouse=True)
def records(tmp_path):
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c001-work", "Campaign")
    campaign.create_campaign(tmp_path, "c002-active", "Other")
    campaign.open_campaign(tmp_path, "c002-active")
    encounter.create_encounter(tmp_path, "c001-work", "e001-first", "[literal] body")
    encounter.create_encounter(tmp_path, "c001-work", "e002-next", "Body")
    region.create_region(tmp_path, "b001", "Region", "Summary")


def invoke(*args):
    return runner.invoke(app, list(args))


def test_qualified_get_context_and_literal_identity():
    result = invoke("encounter", "get", "c001/e001")
    assert result.exit_code == 0, result.output
    assert "[literal] body" in result.output
    assert '"canonical":"e001-first"' in result.output
    assert '"short":"c001/e001"' in result.output
    conflicting = invoke("encounter", "get", "c001/e001", "--campaign", "c002")
    assert conflicting.exit_code == 1
    assert "conflicts" in conflicting.output


def test_cli_mutations_and_unrelated_region_name(tmp_path):
    for args in [
        ("encounter", "update", "c001/e001", "-b", "Updated"),
        ("encounter", "assign-dependency", "c001/e001", "e002"),
        ("encounter", "unassign-dependency", "c001/e001", "c001/e002"),
        ("encounter", "assign-region", "c001/e001", "b001"),
        ("encounter", "review", "c001/e001", "-m", "Reviewed"),
        ("encounter", "record-message", "c001/e001", "-m", "[literal] note"),
        ("encounter", "open", "c001/e001"),
        ("encounter", "complete", "c001/e001"),
    ]:
        result = invoke(*args)
        assert result.exit_code == 0, result.output
        assert '"canonical":"e001-first"' in result.output
    assert encounter.read_encounter(tmp_path, "c001-work", "e001-first").status == "completed"


def test_create_is_literal_and_exact_name_selects_it(tmp_path):
    boss.create_boss(tmp_path, "b001-original", "Original", "Summary")
    result = invoke("boss", "create", "b001", "-b", "New", "-s", "Summary")
    assert result.exit_code == 0, result.output
    assert '"short":"b001"' in result.output
    before = boss.boss_path(tmp_path, "b001-original").read_bytes()
    # Exact canonical name wins: the literal record is updated, never its numbered sibling.
    result = invoke("boss", "update", "b001", "-b", "Updated", "-s", "Summary")
    assert result.exit_code == 0, result.output
    assert boss.read_metadata(tmp_path, "b001")[1] == "Updated"
    assert boss.boss_path(tmp_path, "b001-original").read_bytes() == before
    result = invoke("boss", "update", "b0001", "-b", "No", "-s", "Summary")
    assert result.exit_code == 1 and "Ambiguous" in result.output


def test_list_order_and_prime_selectors():
    for args in [
        ("encounter", "list", "-c", "c001"),
        ("encounter", "order", "-c", "c001"),
        ("prime", "applicable-lore", "c001/e001"),
    ]:
        result = invoke(*args)
        assert result.exit_code == 0, result.output
    result = api.encounter_get("c001/e001")
    assert result["identity"]["short"] == "c001/e001"


def test_unknown_reference_is_readable():
    result = invoke("campaign", "get", "c999")
    assert result.exit_code == 1
    assert "does not exist" in result.output
    assert "Traceback" not in result.output


def test_order_budget_accounts_for_status_and_dependency_fields(tmp_path, monkeypatch):
    encounter.assign_dependency(tmp_path, "c001-work", "e002-next", "e001-first")
    full = api.encounter_order(campaign="c001")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", len(references.encoded(full)) - 1)
    with pytest.raises(references.ReferenceError, match="budget"):
        api.encounter_order(campaign="c001")
    result = invoke("encounter", "order", "-c", "c001")
    assert result.exit_code == 1
    assert "budget" in result.output


def test_cli_campaign_get_selects_exact_short_shaped_legacy_name(tmp_path):
    from cac.core import campaign as campaign_core

    campaign_core.create_campaign(tmp_path, "c001", "Legacy body")
    campaign_core.create_campaign(tmp_path, "c001-mvp", "Numbered body")
    result = runner.invoke(app, ["campaign", "get", "c001"])
    assert result.exit_code == 0, result.output
    assert "Legacy body" in result.output and "Numbered body" not in result.output
