from pathlib import Path

import pytest
from cac.core import boss, campaign, config, encounter, lore, prime, references, region, world


def linked_prime(root):
    world.initialize_world(root)
    boss.create_boss(root, "b001-goal", "[bossbody]", "Boss summary")
    boss.make_available(root, "b001-goal")
    boss.assign_campaign(root, "b001-goal", "c001-work", "Campaign body")
    campaign.open_campaign(root, "c001-work")


@pytest.mark.parametrize("defect", [None, "missing", "malformed", "reverse-only", "competing", "status", "archive"])
def test_prime_active_boss_and_integrity_diagnostics(tmp_path, defect):
    import frontmatter

    linked_prime(tmp_path)
    path = campaign.campaign_path(tmp_path, "c001-work")
    goal_path = boss.boss_path(tmp_path, "b001-goal")
    if defect in ("malformed", "reverse-only"):
        post = frontmatter.load(path)
        if defect == "malformed":
            post["bosses"] = "not-a-list"
        else:
            post.metadata.pop("bosses")
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
    elif defect == "missing":
        goal_path.unlink()
    elif defect == "competing":
        other = campaign.create_campaign(tmp_path, "c002-other", "Other")
        post = frontmatter.load(other)
        post["bosses"] = ["b001-goal"]
        other.write_text(frontmatter.dumps(post), encoding="utf-8")
    elif defect in ("status", "archive"):
        post = frontmatter.load(goal_path)
        post["status" if defect == "status" else "archived"] = "vanquished" if defect == "status" else True
        goal_path.write_text(frontmatter.dumps(post), encoding="utf-8")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*.md")}
    payload = prime.present(prime.assemble_prime(tmp_path))
    if defect is None:
        assert payload["active_bosses"][0] == {
            "metadata": {
                "name": "b001-goal",
                "status": "available",
                "archived": False,
                "depends_on": [],
                "campaign": "c001-work",
            },
            "summary": "Boss summary",
            "body": "[bossbody]",
        }
        assert payload["active_boss_diagnostics"] == []
        assert payload["active_boss_names"] == ["b001-goal"]
    else:
        assert payload["active_bosses"] == []
        assert payload["active_boss_diagnostics"][0]["code"] == "invalid_boss_link"
        assert payload["active_boss_diagnostics"][0]["campaign"] == "c001-work"
    assert {p: p.read_bytes() for p in before} == before


def test_prime_total_budget_preserves_state_and_hydration_refs(tmp_path, monkeypatch):
    linked_prime(tmp_path)
    world.update_body(tmp_path, '🦉"\\' * 5000)
    # Edit the tactical body and boss fixture without changing ownership.
    import frontmatter

    for path in (campaign.campaign_path(tmp_path, "c001-work"), boss.boss_path(tmp_path, "b001-goal")):
        post = frontmatter.load(path)
        post.content = "[content] 🐉" * 5000
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 2200)
    bundle = prime.assemble_prime(tmp_path)
    payload = prime.present(bundle)
    assert len(references.encoded(payload)) <= 2200
    assert payload["active_bosses"][0]["metadata"]["campaign"] == "c001-work"
    assert payload["active_bosses"][0]["summary"] == "Boss summary"
    assert {entry["ref"]["tool"] for entry in payload["truncations"]} == {"world_get", "campaign_get", "boss_get"}
    assert all(entry["notice"] == "TRUNCATED" for entry in payload["truncations"])
    assert all(payload["active_bosses"][0][key] for key in ("body", "metadata", "summary"))
    assert len(bundle.world.body) > 2200  # Presentation does not mutate in-process context.
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 50)
    with pytest.raises(ValueError, match="metadata/state"):
        prime.present(bundle)


def test_prime_routing_entries_are_not_silently_omitted(tmp_path, monkeypatch):
    world.initialize_world(tmp_path)
    for number in range(8):
        region.create_region(tmp_path, f"r{number}", "Body", "routing" * 60, "path")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 1000)
    with pytest.raises(ValueError, match="metadata/state"):
        prime.present(prime.assemble_prime(tmp_path))


def test_assemble_prime_missing_world_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
        prime.assemble_prime(tmp_path)


@pytest.mark.parametrize("override", [False, True])
def test_prime_branch_settings_match_world_without_writes(tmp_path: Path, legacy_world: Path, override: bool) -> None:
    if override:
        world.set_attribute(tmp_path, "planning_branch", "plans/team")
    before = legacy_world.read_bytes()
    modified = legacy_world.stat().st_mtime_ns

    bundle = prime.assemble_prime(tmp_path)

    assert bundle.world == world.read_world(tmp_path)
    assert bundle.world.metadata["merge_target_branch"] == "main"
    assert bundle.world.metadata["planning_branch"] == ("plans/team" if override else "planning")
    assert legacy_world.read_bytes() == before
    assert legacy_world.stat().st_mtime_ns == modified


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
