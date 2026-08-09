from pathlib import Path

import pytest
from cac.core import campaign, encounter, lore, region, world
from cac.mcp import prime as mcp_prime


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
