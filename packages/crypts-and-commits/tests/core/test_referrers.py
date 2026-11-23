from pathlib import Path

import pytest
from cac.core import boss, campaign, coupling, encounter, lore, referrers, region, ruling, search_index, world


def files(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*.md")}


@pytest.fixture
def linked(tmp_path: Path) -> Path:
    """World, two regions and three lore entries cross-assigned, plus encounters in two campaigns."""
    world.initialize_world(tmp_path)
    for name in ("backend", "frontend"):
        region.create_region(tmp_path, name, "Body.", "Summary.")
    for name in ("clean-code", "clean-code-extra", "unused"):
        lore.create_lore(tmp_path, name, "Body.", "Summary.")
    world.assign_lore(tmp_path, "clean-code")
    region.assign_lore(tmp_path, "frontend", "clean-code")
    region.assign_lore(tmp_path, "backend", "clean-code")
    region.assign_lore(tmp_path, "backend", "clean-code-extra")
    for name in ("c001-live", "c002-other"):
        campaign.create_campaign(tmp_path, name, "Tactics.")
    encounter.create_encounter(tmp_path, "c001-live", "e001-api", "Plan.")
    encounter.assign_region(tmp_path, "c001-live", "e001-api", "backend")
    encounter.create_encounter(tmp_path, "c002-other", "e001-ui", "Plan.")
    encounter.assign_region(tmp_path, "c002-other", "e001-ui", "frontend")
    return tmp_path


def test_lore_referrers_list_world_and_regions_sorted(linked: Path) -> None:
    assert referrers.lore_referrers(linked, "clean-code") == [
        "region backend (assigned_lore)",
        "region frontend (assigned_lore)",
        "world (assigned_lore)",
    ]
    # Exact list membership, never substring matching.
    assert referrers.lore_referrers(linked, "clean-code-extra") == ["region backend (assigned_lore)"]
    assert referrers.lore_referrers(linked, "unused") == []


def test_region_referrers_list_lore_and_live_encounters(linked: Path) -> None:
    assert referrers.region_referrers(linked, "backend") == [
        "encounter c001-live/e001-api (regions)",
        "lore clean-code (assigned_regions)",
        "lore clean-code-extra (assigned_regions)",
    ]


def test_archived_campaign_encounters_do_not_block_region_delete(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    region.create_region(tmp_path, "backend", "Body.", "Summary.")
    campaign.create_campaign(tmp_path, "c001-done", "Tactics.")
    encounter.create_encounter(tmp_path, "c001-done", "e001-api", "Plan.")
    encounter.assign_region(tmp_path, "c001-done", "e001-api", "backend")
    encounter.abandon_encounter(tmp_path, "c001-done", "e001-api", "Dropped.")
    campaign.abandon_campaign(tmp_path, "c001-done", "Dropped.")
    campaign.archive_campaign(tmp_path, "c001-done")

    assert referrers.region_referrers(tmp_path, "backend") == []
    region.delete_region(tmp_path, "backend")
    assert not region.exists(tmp_path, "backend")


def test_campaign_referrers_include_live_and_archived_encounters_and_rulings(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c001-work", "Tactics.")
    encounter.create_encounter(tmp_path, "c001-work", "e001-first", "Plan.")
    campaign.open_campaign(tmp_path, "c001-work")
    ruling.create_ruling(tmp_path, "c001-e001-choice", "Decision.", "Summary.", "Developer")
    ruling.create_ruling(tmp_path, "c001-e000-scope", "Decision.", "Summary.", "Developer")
    ruling.note(tmp_path, "c001-e000-scope", "No change needed.")
    ruling.archive_ruling(tmp_path, "c001-e000-scope")
    encounter.abandon_encounter(tmp_path, "c001-work", "e001-first", "Dropped.")
    campaign.abandon_campaign(tmp_path, "c001-work", "Dropped.")
    campaign.archive_campaign(tmp_path, "c001-work")

    assert referrers.campaign_referrers(tmp_path, "c001-work") == [
        "encounter c001-work/e001-first (campaign)",
        "ruling c001-e000-scope (campaign)",
        "ruling c001-e001-choice (campaign)",
    ]


def test_campaign_referrers_without_world_or_records_are_empty(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "c001-empty", "Tactics.")
    assert referrers.campaign_referrers(tmp_path, "c001-empty") == []


@pytest.mark.parametrize(
    ("kind", "name", "listed"),
    [
        ("lore", "clean-code", ["world (assigned_lore)", "region backend (assigned_lore)"]),
        ("region", "backend", ["lore clean-code (assigned_regions)", "encounter c001-live/e001-api (regions)"]),
        ("campaign", "c001-live", ["encounter c001-live/e001-api (campaign)"]),
    ],
)
def test_refused_delete_lists_every_referrer_and_changes_nothing(
    linked: Path, kind: str, name: str, listed: list[str]
) -> None:
    search_index.rebuild_index(linked)
    before, counts = files(linked), search_index.index_counts(linked)
    delete = {"lore": lore.delete_lore, "region": region.delete_region, "campaign": campaign.delete_campaign}[kind]

    with pytest.raises(referrers.ReferencedRecordError) as caught:
        delete(linked, name)

    message = str(caught.value)
    assert message.startswith(f"Cannot delete {kind} {name!r}") and "Unassign or remove" in message
    assert all(entry in message for entry in listed)
    assert files(linked) == before and search_index.index_counts(linked) == counts
    assert search_index.status(linked)["freshness"] == "fresh"


def test_deletes_succeed_once_unreferenced(linked: Path) -> None:
    world.unassign_lore(linked, "clean-code")
    for name in ("backend", "frontend"):
        region.unassign_lore(linked, name, "clean-code")
    lore.delete_lore(linked, "clean-code")
    assert not lore.exists(linked, "clean-code")

    region.unassign_lore(linked, "backend", "clean-code-extra")
    encounter.unassign_region(linked, "c001-live", "e001-api", "backend")
    region.delete_region(linked, "backend")
    assert not region.exists(linked, "backend")

    encounter.delete_encounter(linked, "c001-live", "e001-api")
    campaign.delete_campaign(linked, "c001-live")
    assert not campaign.exists(linked, "c001-live")


def test_boss_guard_still_runs_before_referrer_guard(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    boss.create_boss(tmp_path, "b001-goal", "Design.", "Summary.")
    boss.make_available(tmp_path, "b001-goal")
    campaign.create_campaign(tmp_path, "c001-work", "Tactics.", ["b001"])
    encounter.create_encounter(tmp_path, "c001-work", "e001-first", "Plan.")
    with pytest.raises(coupling.CampaignLinkedError):
        campaign.delete_campaign(tmp_path, "c001-work")
