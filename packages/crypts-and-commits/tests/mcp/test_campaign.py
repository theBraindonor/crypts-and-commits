from pathlib import Path

import pytest
from cac.core import campaign, encounter, region
from cac.mcp import campaign as mcp_campaign


def test_campaign_get_returns_metadata_and_body(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "mvp", "Campaign body.")

    result = mcp_campaign.campaign_get("mvp")

    assert result["body"].strip() == "Campaign body."
    assert result["metadata"]["status"] == "draft"


def test_campaign_get_missing_raises() -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        mcp_campaign.campaign_get("missing")


def test_campaign_list_returns_items_and_cursor(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "mvp", "Body.")
    campaign.create_campaign(tmp_path, "payments", "Body.")
    campaign.open_campaign(tmp_path, "mvp")

    result = mcp_campaign.campaign_list()

    assert result["items"] == [{"name": "mvp", "status": "open"}, {"name": "payments", "status": "draft"}]
    assert result["next_cursor"] is None


def test_campaign_create_returns_new_campaign() -> None:
    result = mcp_campaign.campaign_create("mvp", "Campaign body.")

    assert result == {"name": "mvp", "status": "draft", "archived": False, "body": "Campaign body."}


def test_campaign_update_replaces_body(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "mvp", "Old.")

    result = mcp_campaign.campaign_update("mvp", "New.")

    assert result["body"].strip() == "New."


def test_campaign_delete_removes_file(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "mvp", "Body.")

    result = mcp_campaign.campaign_delete("mvp")

    assert not campaign.exists(tmp_path, "mvp")
    assert result["deleted"].endswith("mvp.md")


def test_campaign_open_and_pause(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "mvp", "Body.")

    opened = mcp_campaign.campaign_open("mvp")
    assert opened["status"] == "open"

    paused = mcp_campaign.campaign_pause("mvp")
    assert paused["status"] == "paused"


def test_campaign_complete_requires_message(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "mvp", "Body.")
    campaign.open_campaign(tmp_path, "mvp")

    result = mcp_campaign.campaign_complete("mvp", "Shipped it.")

    assert result["status"] == "completed"


def test_campaign_abandon_records_postmortem(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "mvp", "Body.")

    result = mcp_campaign.campaign_abandon("mvp", "Cutting scope.")

    assert result["status"] == "abandoned"
    assert "Cutting scope." in result["body"]


def _complete_campaign_with_encounter(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "mvp", "Body.")
    campaign.open_campaign(tmp_path, "mvp")
    encounter.create_encounter(tmp_path, "mvp", "goblin-ambush", "Body.")
    region.create_region(tmp_path, "default-region", "Body.", "Summary.")
    encounter.assign_region(tmp_path, "mvp", "goblin-ambush", "default-region")
    encounter.review_encounter(tmp_path, "mvp", "goblin-ambush", "ok")
    encounter.open_encounter(tmp_path, "mvp", "goblin-ambush")
    encounter.complete_encounter(tmp_path, "mvp", "goblin-ambush")
    campaign.complete_campaign(tmp_path, "mvp", "Shipped.")


def test_campaign_archive_moves_campaign_and_encounter(tmp_path: Path) -> None:
    _complete_campaign_with_encounter(tmp_path)

    result = mcp_campaign.campaign_archive("mvp")

    assert result["archived"] is True
    assert result["status"] == "completed"
    assert result["archived_encounters"] == ["goblin-ambush"]
    assert not (tmp_path / ".sourcebook" / "campaigns" / "mvp.md").exists()
    assert (tmp_path / ".sourcebook" / "archive" / "campaigns" / "mvp.md").exists()


def test_campaign_archive_missing_raises() -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        mcp_campaign.campaign_archive("missing")


def test_campaign_archive_rejects_non_terminal(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "mvp", "Body.")

    with pytest.raises(campaign.CampaignNotTerminalError):
        mcp_campaign.campaign_archive("mvp")


def test_campaign_archive_rejects_unfinished_encounters(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "mvp", "Body.")
    campaign.open_campaign(tmp_path, "mvp")
    encounter.create_encounter(tmp_path, "mvp", "dragon-hoard", "Body.")
    campaign.complete_campaign(tmp_path, "mvp", "Shipped.")

    with pytest.raises(campaign.CampaignHasUnfinishedEncountersError, match="dragon-hoard"):
        mcp_campaign.campaign_archive("mvp")


def test_campaign_archive_rejects_already_archived(tmp_path: Path) -> None:
    _complete_campaign_with_encounter(tmp_path)
    mcp_campaign.campaign_archive("mvp")

    with pytest.raises(campaign.CampaignAlreadyArchivedError):
        mcp_campaign.campaign_archive("mvp")


def test_campaign_get_still_works_after_archiving(tmp_path: Path) -> None:
    _complete_campaign_with_encounter(tmp_path)
    mcp_campaign.campaign_archive("mvp")

    result = mcp_campaign.campaign_get("mvp")

    assert result["metadata"]["archived"] is True
