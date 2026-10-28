import frontmatter
import pytest
from cac.core import boss, campaign, config, encounter, references, region, world
from cac.mcp import boss as bosses
from cac.mcp import campaign as campaigns
from cac.mcp import encounter as encounters
from cac.mcp import prime


@pytest.fixture(autouse=True)
def records(tmp_path):
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c001-first", "Campaign")
    campaign.create_campaign(tmp_path, "c002-second", "Campaign")
    campaign.open_campaign(tmp_path, "c002-second")
    encounter.create_encounter(tmp_path, "c001-first", "e001-first", "Body")
    encounter.create_encounter(tmp_path, "c001-first", "e002-second", "Body")
    region.create_region(tmp_path, "b001", "Region body", "Summary")


def test_qualified_get_update_dependencies_and_lifecycle(tmp_path):
    result = encounters.encounter_get("c001/e001")
    assert result["metadata"]["name"] == "e001-first"
    assert result["identity"] == {
        "canonical": "e001-first",
        "campaign": "c001-first",
        "short": "c001/e001",
        "bare_short": "e001",
        "reason": None,
    }
    assert encounters.encounter_update("c001/e001", "Updated")["body"] == "Updated"
    encounters.encounter_assign_dependency("c001/e001", "c001/e002")
    assert encounter.read_metadata(tmp_path, "c001-first", "e001-first")[0]["depends_on"] == ["e002-second"]
    encounters.encounter_unassign_dependency("e001", "e002", campaign="c001")
    encounters.encounter_assign_region("c001/e001", "b001")
    encounters.encounter_review("c001/e001", "Reviewed")
    encounters.encounter_record_message("c001/e001", "[tool.ruff] note")
    encounters.encounter_open("c001/e001")
    encounters.encounter_complete("c001/e001")
    assert encounter.read_encounter(tmp_path, "c001-first", "e001-first").status == "completed"
    with pytest.raises(references.ReferenceError, match="conflicts"):
        encounters.encounter_get("c001/e001", campaign="c002")
    with pytest.raises(campaign.InvalidCampaignTransitionError):
        campaigns.campaign_complete("c001", "Complete")


def test_creations_are_literal_and_campaign_selection_is_short(tmp_path):
    result = encounters.encounter_create("e003", "Literal new name", campaign="c001")
    assert result["name"] == "e003"
    assert result["campaign"] == "c001-first"
    bosses.boss_create("b001-existing", "Body", "Summary")
    result = bosses.boss_create("b001", "New literal", "Summary")
    assert result["metadata"]["name"] == "b001"
    assert result["identity"]["short"] == "b001"
    assert result["identity"]["reason"] is None
    assert bosses.boss_get("b001-existing")["identity"]["reason"] == "ambiguous"
    assert boss.read_metadata(tmp_path, "b001-existing")[1] == "Body"


def test_boss_mixed_refs_and_missing_edge_repair(tmp_path):
    bosses.boss_create("b001-source", "Body", "Summary")
    bosses.boss_create("b002-target", "Body", "Summary")
    bosses.boss_assign_dependency("b001", "b002-target")
    assert bosses.boss_get("b001")["metadata"]["depends_on"] == ["b002-target"]
    path = boss.boss_path(tmp_path, "b001-source")
    post = frontmatter.load(path)
    post["depends_on"].append("deleted-canonical")
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    bosses.boss_unassign_dependency("b001", "deleted-canonical")
    with pytest.raises(boss.BossError):
        bosses.boss_assign_dependency("b001", "b001-source")
    assert bosses.boss_candidates()["items"][0]["identity"]["short"] == "b001"


def test_prime_selector_and_lists_expose_identity(tmp_path):
    encounters.encounter_assign_region("c001/e001", "b001")
    assert prime.prime_applicable_lore("c001/e001") == []
    page = encounters.encounter_list(campaign="c001")
    assert page["items"] == ["e001-first", "e002-second"]
    assert [value["short"] for value in page["identities"]] == ["c001/e001", "c001/e002"]
    assert campaigns.campaign_get("c001")["identity"]["short"] == "c001"


def test_every_shipped_selector_uses_shared_contract():
    for module, prefix in ((bosses, "boss_"), (campaigns, "campaign_"), (encounters, "encounter_")):
        for name, value in vars(module).items():
            if name.startswith(prefix) and callable(value) and not name.endswith("_to_dict"):
                assert hasattr(value, "reference_contract"), name
    assert prime.prime_applicable_lore.reference_contract["domain"] == "encounter"


def test_numbered_boss_lifecycle_and_archived_get():
    bosses.boss_create("b001-goal", "Body", "Summary")
    assert bosses.boss_make_available("b001")["metadata"]["status"] == "available"
    assert bosses.boss_update("b001", "New", "Updated")["body"] == "New"
    bosses.boss_withdraw("b001")
    bosses.boss_reactivate("b001")
    bosses.boss_withdraw("b001")
    archived = bosses.boss_archive("b001")
    assert archived["metadata"]["archived"] is True
    assert archived["identity"]["canonical"] == "b001-goal"
    assert bosses.boss_get("b001")["identity"]["short"] == "b001"
    with pytest.raises(boss.BossError):
        bosses.boss_reactivate("b001")


def test_campaign_lifecycle_archive_and_qualified_archive_reads(tmp_path):
    campaigns.campaign_pause("c002")
    campaigns.campaign_update("c001", "Updated campaign")
    campaigns.campaign_open("c001")
    campaigns.campaign_pause("c001")
    campaigns.campaign_open("c001")
    encounters.encounter_abandon("c001/e001", "Not needed")
    encounters.encounter_abandon("c001/e002", "Not needed")
    campaigns.campaign_complete("c001", "Complete")
    campaigns.campaign_archive("c001")
    assert campaigns.campaign_get("c001")["metadata"]["archived"] is True
    assert encounters.encounter_get("c001/e001")["metadata"]["archived"] is True
    with pytest.raises(campaign.CampaignNotMutableError):
        encounters.encounter_update("c001/e001", "No")


def test_shipped_deletes_and_missing_encounter_dependency_removal(tmp_path):
    path = encounter.encounter_path(tmp_path, "c001-first", "e001-first")
    post = frontmatter.load(path)
    post["depends_on"] = ["deleted-canonical"]
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    result = encounters.encounter_unassign_dependency("c001/e001", "deleted-canonical")
    assert result["depends_on"] == []
    assert encounters.encounter_delete("c001/e002")["identity"]["canonical"] == "e002-second"
    campaigns.campaign_create("c003-delete", "Temporary")
    assert campaigns.campaign_delete("c003")["identity"]["canonical"] == "c003-delete"
    campaigns.campaign_create("c004-abandon", "Temporary")
    assert campaigns.campaign_abandon("c004", "Not needed")["status"] == "abandoned"


def test_response_bodies_reserve_identity_before_truncation(tmp_path, monkeypatch):
    bosses.boss_create("b001-goal", "x" * 4000, "Summary")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 1000)
    result = bosses.boss_get("b001")
    assert "TRUNCATED" in result["notice"]
    assert result["identity"]["canonical"] == "b001-goal"
    assert len(references.encoded(result)) <= 1000


def test_campaign_get_selects_exact_short_shaped_legacy_name(tmp_path):
    from cac.mcp import campaign as campaign_mcp

    campaign_mcp.campaign_create("c001", "Legacy")
    campaign_mcp.campaign_create("c001-mvp", "Numbered")
    assert campaign_mcp.campaign_get("c001")["body"] == "Legacy"
    assert campaign_mcp.campaign_get("c001-mvp")["identity"]["reason"] == "ambiguous"
