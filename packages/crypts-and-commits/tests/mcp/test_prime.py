from pathlib import Path

import pytest
from cac.core import campaign, encounter, lore, region, world
from cac.mcp import prime as mcp_prime
from cac.mcp import world as mcp_world


def test_prime_boss_matches_shared_core_presentation(tmp_path):
    from cac.core import boss, prime

    world.initialize_world(tmp_path)
    boss.create_boss(tmp_path, "b001-goal", "[literal]", "Summary")
    boss.make_available(tmp_path, "b001-goal")
    boss.assign_campaign(tmp_path, "b001-goal", "c001-work", "Campaign")
    campaign.open_campaign(tmp_path, "c001-work")
    assert mcp_prime.prime_get() == prime.present(prime.assemble_prime(tmp_path))
    assert mcp_prime.prime_get()["active_boss"]["body"] == "[literal]"


@pytest.mark.parametrize("override", [False, True])
def test_prime_world_branch_settings_agree_with_world_tool(legacy_world: Path, override: bool) -> None:
    if override:
        mcp_world.world_set("merge_target_branch", "release/next")
    before = legacy_world.read_bytes()

    result = mcp_prime.prime_get()

    assert set(result) == {
        "world",
        "world_lore",
        "regions",
        "active_campaign",
        "campaign_body",
        "active_boss",
        "active_boss_diagnostic",
        "truncations",
    }
    assert result["world"] == mcp_world.world_get()
    assert result["world"]["metadata"]["merge_target_branch"] == ("release/next" if override else "main")
    assert result["world"]["metadata"]["planning_branch"] == "planning"
    assert legacy_world.read_bytes() == before


def test_prime_get_assembles_bundle(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "world-lore", "Body.", "World lore summary.")
    world.assign_lore(tmp_path, "world-lore")
    region.create_region(tmp_path, "northlands", "Body.", "Region summary.", "src/north")
    campaign.create_campaign(tmp_path, "opening-gambit", "Campaign body.")
    campaign.open_campaign(tmp_path, "opening-gambit")

    result = mcp_prime.prime_get()

    assert result["world_lore"] == [{"name": "world-lore", "summary": "World lore summary."}]
    assert result["regions"] == [
        {"name": "northlands", "summary": "Region summary.", "path": "src/north", "assigned_lore": []}
    ]
    assert result["active_campaign"] == "opening-gambit"
    assert result["campaign_body"].strip() == "Campaign body."


def test_prime_get_no_active_campaign(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = mcp_prime.prime_get()

    assert result["active_campaign"] is None
    assert result["campaign_body"] is None


def test_prime_applicable_lore_defaults_to_active_campaign(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    lore.create_lore(tmp_path, "world-lore", "Body.", "World lore summary.")
    world.assign_lore(tmp_path, "world-lore")

    result = mcp_prime.prime_applicable_lore("goblin-ambush")

    assert result == [{"name": "world-lore", "summary": "World lore summary.", "ref": "world-lore"}]


def test_prime_applicable_lore_explicit_campaign(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = mcp_prime.prime_applicable_lore("goblin-ambush", campaign="opening-gambit")

    assert result == []


def test_prime_applicable_lore_no_active_campaign_raises(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    with pytest.raises(campaign.NoActiveCampaignError):
        mcp_prime.prime_applicable_lore("goblin-ambush")


def test_prime_applicable_lore_missing_encounter_raises(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")

    with pytest.raises(encounter.EncounterNotFoundError):
        mcp_prime.prime_applicable_lore("missing")
