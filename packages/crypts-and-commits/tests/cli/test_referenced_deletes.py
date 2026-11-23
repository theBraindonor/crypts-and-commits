from pathlib import Path

import pytest
from cac.cli.app import app
from cac.core import campaign, encounter, lore, referrers, region, world
from cac.mcp import campaign as mcp_campaign
from cac.mcp import lore as mcp_lore
from cac.mcp import region as mcp_region
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture
def linked(tmp_path: Path) -> Path:
    world.initialize_world(tmp_path)
    region.create_region(tmp_path, "backend", "Body.", "Summary.")
    lore.create_lore(tmp_path, "clean-code", "Body.", "Summary.")
    world.assign_lore(tmp_path, "clean-code")
    region.assign_lore(tmp_path, "backend", "clean-code")
    campaign.create_campaign(tmp_path, "c001-work", "Tactics.")
    encounter.create_encounter(tmp_path, "c001-work", "e001-api", "Plan.")
    encounter.assign_region(tmp_path, "c001-work", "e001-api", "backend")
    return tmp_path


@pytest.mark.parametrize(
    ("command", "name", "mcp_delete"),
    [
        ("lore", "clean-code", mcp_lore.lore_delete),
        ("region", "backend", mcp_region.region_delete),
        ("campaign", "c001-work", mcp_campaign.campaign_delete),
    ],
)
def test_cli_and_mcp_refuse_referenced_deletes_with_the_same_message(
    linked: Path, command: str, name: str, mcp_delete
) -> None:
    with pytest.raises(referrers.ReferencedRecordError) as mcp_error:
        mcp_delete(name)

    result = runner.invoke(app, [command, "delete", name, "--yes"])

    assert result.exit_code == 1
    assert str(mcp_error.value) == " ".join(result.output.split())
    assert {"lore": lore.exists, "region": region.exists, "campaign": campaign.exists}[command](linked, name)


def test_cli_and_mcp_delete_unreferenced_records(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    for name in ("one", "two"):
        lore.create_lore(tmp_path, name, "Body.", "Summary.")
        region.create_region(tmp_path, name, "Body.", "Summary.")
        campaign.create_campaign(tmp_path, f"c00{1 if name == 'one' else 2}-{name}", "Tactics.")

    assert runner.invoke(app, ["lore", "delete", "one", "--yes"]).exit_code == 0
    assert runner.invoke(app, ["region", "delete", "one", "--yes"]).exit_code == 0
    assert runner.invoke(app, ["campaign", "delete", "c001-one", "--yes"]).exit_code == 0
    mcp_lore.lore_delete("two")
    mcp_region.region_delete("two")
    mcp_campaign.campaign_delete("c002-two")
    assert lore.list_lore(tmp_path) == [] and region.list_regions(tmp_path) == []
    assert campaign.list_campaigns(tmp_path) == []
