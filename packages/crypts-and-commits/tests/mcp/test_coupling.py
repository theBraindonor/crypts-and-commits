import frontmatter
import pytest
from cac.core import boss, campaign, coupling, world
from cac.mcp import boss as bosses
from cac.mcp import campaign as campaigns


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)
    bosses.boss_create("b001-goal", "[aspirational] goal", "Summary")
    bosses.boss_make_available("b001")


def test_promotion_lifecycle_and_inspection(tmp_path):
    assigned = bosses.boss_assign_campaign("b001", "c001-work", "[tactical] plan")
    assert assigned["campaign"] == "c001-work" and assigned["status"] == "draft"
    assert assigned["identity"]["short"] == "b001"
    assert assigned["campaign_identity"]["short"] == "c001"
    assert campaigns.campaign_get("c001")["boss_link"]["kind"] == "current"
    campaigns.campaign_open("c001")
    campaigns.campaign_complete("c001", "First")
    result = campaigns.campaign_reactivate("c001", "[feedback]")
    assert result["status"] == "open" and result["bosses"] == ["b001-goal"]
    assert "[feedback]" in result["body"]
    assert campaigns.campaign_update("c001", result["body"] + "\nFix")["bosses"] == ["b001-goal"]
    campaigns.campaign_complete("c001", "Again")
    campaigns.campaign_archive("c001")
    assert bosses.boss_get("b001")["metadata"]["archived"] is True
    assert bosses.boss_assign_campaign("b001", "c001-work", "Do not overwrite")["reused"] is True
    with pytest.raises(coupling.CampaignLinkedError):
        campaigns.campaign_delete("c001")


def test_literal_campaign_creation_name_and_broken_origin_diagnostics(tmp_path):
    campaigns.campaign_create("c001-existing", "Existing")
    result = bosses.boss_assign_campaign("b001", "c001", "Literal")
    assert result["campaign"] == "c001"
    assert result["campaign_identity"]["short"] is None
    path = campaign.campaign_path(tmp_path, "c001")
    post = frontmatter.load(path)
    post["bosses"] = ["missing-goal"]
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    inspected = campaigns.campaign_get("c001-existing")
    # The malformed link is surfaced rather than mutating or inferring an assignment.
    assert inspected["metadata"]["name"] == "c001-existing"
    assert coupling.inspection(tmp_path, "c001")["kind"] == "invalid"
    with pytest.raises(coupling.LinkError):
        campaign.open_campaign(tmp_path, "c001")


def test_abandon_releases_current_link_but_retains_origin(tmp_path):
    bosses.boss_assign_campaign("b001", "c001-work", "First")
    campaigns.campaign_abandon("c001", "Cancelled")
    assert "campaign" not in bosses.boss_get("b001")["metadata"]
    result = campaigns.campaign_get("c001")
    assert result["metadata"]["bosses"] == ["b001-goal"]
    assert result["boss_link"]["kind"] == "historical"
    bosses.boss_assign_campaign("b001", "c002-new", "Second")
    campaigns.campaign_archive("c001")
    assert boss.read_metadata(tmp_path, "b001-goal")[0]["campaign"] == "c002-new"
