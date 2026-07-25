from datetime import UTC, datetime
from pathlib import Path

import pytest
from cac.core import campaign, encounter, frontmatter_utils, git_utils, lore, prime, region, world

_FIXED_TIME = datetime(2026, 7, 23, 18, 4, 12, tzinfo=UTC)


def _set_identity(monkeypatch: pytest.MonkeyPatch, *, user: str = "John Hoff", when: datetime = _FIXED_TIME) -> None:
    monkeypatch.setattr(git_utils, "current_git_user", lambda root: user)
    monkeypatch.setattr(frontmatter_utils, "utcnow", lambda: when)


@pytest.fixture(autouse=True)
def _default_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_identity(monkeypatch)


def test_assemble_prime_missing_world_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
        prime.assemble_prime(tmp_path)


def test_assemble_prime_returns_world_full_body(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    world.update_body(tmp_path, "The world body.")

    bundle = prime.assemble_prime(tmp_path)

    assert bundle.world.body.strip() == "The world body."


def test_assemble_prime_includes_only_enabled_world_assigned_lore(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "enabled-lore", "Body.", "Enabled summary.")
    lore.create_lore(tmp_path, "disabled-lore", "Body.", "Disabled summary.")
    world.assign_lore(tmp_path, "enabled-lore")
    world.assign_lore(tmp_path, "disabled-lore")
    lore.set_enabled(tmp_path, "disabled-lore", False)

    bundle = prime.assemble_prime(tmp_path)

    assert [entry.name for entry in bundle.world_lore] == ["enabled-lore"]
    assert bundle.world_lore[0].summary == "Enabled summary."


def test_assemble_prime_excludes_region_only_lore_from_world_lore(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.", "Region summary.")
    lore.create_lore(tmp_path, "region-lore", "Body.", "Region lore summary.")
    region.assign_lore(tmp_path, "northlands", "region-lore")

    bundle = prime.assemble_prime(tmp_path)

    assert bundle.world_lore == []


def test_assemble_prime_region_map_carries_edges_not_lore_summaries(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.", "Region summary.", "src/north")
    lore.create_lore(tmp_path, "region-lore", "Body.", "Region lore summary.")
    region.assign_lore(tmp_path, "northlands", "region-lore")

    bundle = prime.assemble_prime(tmp_path)

    assert len(bundle.regions) == 1
    entry = bundle.regions[0]
    assert entry.name == "northlands"
    assert entry.path == "src/north"
    assert entry.summary == "Region summary."
    assert entry.assigned_lore == ["region-lore"]
    # Edges only: the lore's own summary text must not appear anywhere on the entry.
    assert "Region lore summary." not in (entry.summary, str(entry.assigned_lore))


def test_assemble_prime_region_with_no_assigned_lore(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.", "Region summary.")

    bundle = prime.assemble_prime(tmp_path)

    assert bundle.regions[0].assigned_lore == []


def test_assemble_prime_no_active_campaign(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    bundle = prime.assemble_prime(tmp_path)

    assert bundle.active_campaign is None
    assert bundle.campaign_body is None


def test_assemble_prime_active_campaign_body_not_encounters(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Campaign body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Encounter body.")

    bundle = prime.assemble_prime(tmp_path)

    assert bundle.active_campaign == "opening-gambit"
    assert bundle.campaign_body.strip() == "Campaign body."
    assert "goblin-ambush" not in bundle.campaign_body
    # PrimeBundle has no encounter-list field at all - the encounter list is a
    # separate, on-demand call and never part of prime.
    assert not hasattr(bundle, "encounters")


def test_applicable_lore_missing_encounter_raises(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    with pytest.raises(encounter.EncounterNotFoundError):
        prime.applicable_lore(tmp_path, "opening-gambit", "missing")


def test_applicable_lore_includes_world_assigned_lore(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    lore.create_lore(tmp_path, "world-lore", "Body.", "World lore summary.")
    world.assign_lore(tmp_path, "world-lore")

    entries = prime.applicable_lore(tmp_path, "opening-gambit", "goblin-ambush")

    assert [(entry.name, entry.summary, entry.ref) for entry in entries] == [
        ("world-lore", "World lore summary.", "world-lore")
    ]


def test_applicable_lore_includes_region_assigned_lore_for_encounters_region(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    region.create_region(tmp_path, "northlands", "Body.", "Region summary.")
    lore.create_lore(tmp_path, "region-lore", "Body.", "Region lore summary.")
    region.assign_lore(tmp_path, "northlands", "region-lore")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    entries = prime.applicable_lore(tmp_path, "opening-gambit", "goblin-ambush")

    assert [entry.name for entry in entries] == ["region-lore"]


def test_applicable_lore_excludes_other_regions_lore(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    region.create_region(tmp_path, "northlands", "Body.", "Region summary.")
    region.create_region(tmp_path, "southlands", "Body.", "Region summary.")
    lore.create_lore(tmp_path, "south-lore", "Body.", "South lore summary.")
    region.assign_lore(tmp_path, "southlands", "south-lore")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    entries = prime.applicable_lore(tmp_path, "opening-gambit", "goblin-ambush")

    assert entries == []


def test_applicable_lore_excludes_disabled_lore(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    lore.create_lore(tmp_path, "world-lore", "Body.", "World lore summary.")
    world.assign_lore(tmp_path, "world-lore")
    lore.set_enabled(tmp_path, "world-lore", False)

    entries = prime.applicable_lore(tmp_path, "opening-gambit", "goblin-ambush")

    assert entries == []


def test_applicable_lore_deduplicates_lore_assigned_to_both_world_and_region(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    region.create_region(tmp_path, "northlands", "Body.", "Region summary.")
    lore.create_lore(tmp_path, "shared-lore", "Body.", "Shared summary.")
    world.assign_lore(tmp_path, "shared-lore")
    region.assign_lore(tmp_path, "northlands", "shared-lore")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    entries = prime.applicable_lore(tmp_path, "opening-gambit", "goblin-ambush")

    assert [entry.name for entry in entries] == ["shared-lore"]
