from pathlib import Path

import pytest
from cac.core import campaign, git_utils
from cac.mcp import campaign as mcp_campaign


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def _default_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(git_utils, "current_git_user", lambda root: "John Hoff")


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

    assert result == {"name": "mvp", "status": "draft", "body": "Campaign body."}


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
