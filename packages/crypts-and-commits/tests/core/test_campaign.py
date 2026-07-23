from pathlib import Path

import pytest

from cac.core import campaign


def test_list_campaigns_returns_empty_when_no_directory(tmp_path: Path) -> None:
    assert campaign.list_campaigns(tmp_path) == []


def test_create_campaign_writes_frontmatter_and_body(tmp_path: Path) -> None:
    path = campaign.create_campaign(tmp_path, "opening-gambit", "# Opening Gambit\n\nThe party sets out.")

    assert path == tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: opening-gambit" in text
    assert "status: draft" in text
    assert "The party sets out." in text


def test_create_campaign_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(campaign.InvalidCampaignNameError):
        campaign.create_campaign(tmp_path, "bad name!", "body")


def test_create_campaign_allows_periods(tmp_path: Path) -> None:
    path = campaign.create_campaign(tmp_path, "v0.1.0-bootstrapping", "body")

    assert path == tmp_path / ".sourcebook" / "campaigns" / "v0.1.0-bootstrapping.md"


@pytest.mark.parametrize("name", [".", ".."])
def test_create_campaign_rejects_reserved_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(campaign.InvalidCampaignNameError):
        campaign.create_campaign(tmp_path, name, "body")


def test_create_campaign_rejects_duplicate_name(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "duplicate", "first")

    with pytest.raises(campaign.CampaignAlreadyExistsError):
        campaign.create_campaign(tmp_path, "duplicate", "second")


def test_list_campaigns_returns_sorted_names(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "zeta", "z")
    campaign.create_campaign(tmp_path, "alpha", "a")

    assert campaign.list_campaigns(tmp_path) == ["alpha", "zeta"]


def test_template_body_returns_placeholder_text() -> None:
    assert "This campaign has not been described yet." in campaign.template_body()


def test_exists_reflects_created_campaign(tmp_path: Path) -> None:
    assert campaign.exists(tmp_path, "opening-gambit") is False

    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    assert campaign.exists(tmp_path, "opening-gambit") is True


def test_exists_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(campaign.InvalidCampaignNameError):
        campaign.exists(tmp_path, "bad name!")


def test_read_campaign_returns_name_status_and_body(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body text.")

    result = campaign.read_campaign(tmp_path, "opening-gambit")

    assert result.name == "opening-gambit"
    assert result.status == "draft"
    assert result.body.strip() == "Body text."


def test_read_campaign_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.read_campaign(tmp_path, "missing")


def test_read_metadata_returns_full_frontmatter_and_body(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body text.")
    campaign.set_status(tmp_path, "opening-gambit", "open")

    metadata, body = campaign.read_metadata(tmp_path, "opening-gambit")

    assert metadata["name"] == "opening-gambit"
    assert metadata["status"] == "open"
    assert body.strip() == "Body text."


def test_read_metadata_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.read_metadata(tmp_path, "missing")


def test_update_campaign_replaces_body(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Original.")

    campaign.update_campaign(tmp_path, "opening-gambit", "Updated.")

    assert campaign.read_campaign(tmp_path, "opening-gambit").body.strip() == "Updated."


def test_update_campaign_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.update_campaign(tmp_path, "missing", "body")


def test_delete_campaign_removes_file(tmp_path: Path) -> None:
    path = campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    campaign.delete_campaign(tmp_path, "opening-gambit")

    assert not path.exists()


def test_delete_campaign_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.delete_campaign(tmp_path, "missing")


def test_set_status_updates_status(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    result = campaign.set_status(tmp_path, "opening-gambit", "open")

    assert result.status == "open"
    assert campaign.read_campaign(tmp_path, "opening-gambit").status == "open"


def test_set_status_rejects_invalid_status(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    with pytest.raises(campaign.InvalidCampaignStatusError):
        campaign.set_status(tmp_path, "opening-gambit", "cancelled")


def test_set_status_missing_campaign_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.set_status(tmp_path, "missing", "open")


def test_set_status_allows_abandoned(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    result = campaign.set_status(tmp_path, "opening-gambit", "abandoned")

    assert result.status == "abandoned"
