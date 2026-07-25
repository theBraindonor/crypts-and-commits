from pathlib import Path

import pytest
from cac.core import campaign, encounter, git_utils, lore, region, world
from cac.mcp import server


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def _default_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(git_utils, "current_git_user", lambda root: "John Hoff")


def test_world_get_returns_metadata_and_body(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    world.update_body(tmp_path, "The world body.")

    result = server.world_get()

    assert result["body"].strip() == "The world body."
    assert result["metadata"]["name"]


def test_world_get_missing_world_raises() -> None:
    with pytest.raises(world.WorldNotFoundError):
        server.world_get()


def test_world_set_updates_attribute(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = server.world_set("name", "New Name")

    assert result["metadata"]["name"] == "New Name"


def test_world_set_body_replaces_body(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = server.world_set_body("Replaced body.")

    assert result["body"].strip() == "Replaced body."


def test_prime_get_assembles_bundle(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "world-lore", "Body.", "World lore summary.")
    world.assign_lore(tmp_path, "world-lore")
    region.create_region(tmp_path, "northlands", "Body.", "Region summary.", "src/north")
    campaign.create_campaign(tmp_path, "opening-gambit", "Campaign body.")
    campaign.open_campaign(tmp_path, "opening-gambit")

    result = server.prime_get()

    assert result["world_lore"] == [{"name": "world-lore", "summary": "World lore summary."}]
    assert result["regions"] == [
        {"name": "northlands", "summary": "Region summary.", "path": "src/north", "assigned_lore": []}
    ]
    assert result["active_campaign"] == "opening-gambit"
    assert result["campaign_body"].strip() == "Campaign body."


def test_prime_get_no_active_campaign(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = server.prime_get()

    assert result["active_campaign"] is None
    assert result["campaign_body"] is None


def test_prime_applicable_lore_defaults_to_active_campaign(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    lore.create_lore(tmp_path, "world-lore", "Body.", "World lore summary.")
    world.assign_lore(tmp_path, "world-lore")

    result = server.prime_applicable_lore("goblin-ambush")

    assert result == [{"name": "world-lore", "summary": "World lore summary.", "ref": "world-lore"}]


def test_prime_applicable_lore_explicit_campaign(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = server.prime_applicable_lore("goblin-ambush", campaign="opening-gambit")

    assert result == []


def test_prime_applicable_lore_no_active_campaign_raises(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    with pytest.raises(campaign.NoActiveCampaignError):
        server.prime_applicable_lore("goblin-ambush")


def test_prime_applicable_lore_missing_encounter_raises(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")

    with pytest.raises(encounter.EncounterNotFoundError):
        server.prime_applicable_lore("missing")
