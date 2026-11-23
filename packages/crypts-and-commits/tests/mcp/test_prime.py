from pathlib import Path

import pytest
from cac.core import budget, campaign, encounter, lore, references, region, world
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
    assert mcp_prime.prime_get()["active_bosses"][0]["body"] == "[literal]"


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
        "active_bosses",
        "active_boss_diagnostics",
        "active_boss_names",
        "recorded_rulings",
        "recorded_ruling_count",
        "ruling_diagnostics",
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

    assert result == {
        "items": [{"name": "world-lore", "summary": "World lore summary.", "ref": "world-lore"}],
        "next_cursor": None,
        "identity": result["identity"],
    }
    assert result["identity"]["canonical"] == "goblin-ambush"
    assert "identities" not in result


def test_prime_applicable_lore_explicit_campaign(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = mcp_prime.prime_applicable_lore("goblin-ambush", campaign="opening-gambit")

    assert {key: result[key] for key in ("items", "next_cursor")} == {"items": [], "next_cursor": None}


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


def test_prime_get_returns_recorded_rulings_matching_core(tmp_path):
    from cac.core import prime, ruling

    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c002-rulings", "Tactics")
    campaign.open_campaign(tmp_path, "c002-rulings")
    ruling.create_ruling(tmp_path, "c002-e000-scope", "Body", "Summary", "GM")
    result = mcp_prime.prime_get()
    assert result == prime.present(prime.assemble_prime(tmp_path))
    assert result["recorded_rulings"] == [
        {"name": "c002-e000-scope", "campaign": "c002-rulings", "encounter": None, "summary": "Summary"}
    ]
    assert result["recorded_ruling_count"] == 1 and result["ruling_diagnostics"] == []


def _many_lore(root: Path, count: int) -> None:
    world.initialize_world(root)
    campaign.create_campaign(root, "opening-gambit", "Body.")
    campaign.open_campaign(root, "opening-gambit")
    encounter.create_encounter(root, "opening-gambit", "goblin-ambush", "Body.")
    for index in range(count):
        name = f"lore-{index:02d}"
        lore.create_lore(root, name, "Body.", f"Summary {index} " + "x" * 60)
        world.assign_lore(root, name)


def test_prime_applicable_lore_pages_within_json_budget(tmp_path: Path, monkeypatch) -> None:
    _many_lore(tmp_path, 12)
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 400)

    pages, cursor = [], None
    while True:
        result = mcp_prime.prime_applicable_lore("goblin-ambush", cursor=cursor)
        assert len(references.encoded(result)) <= 400
        pages.append([item["name"] for item in result["items"]])
        cursor = result["next_cursor"]
        if cursor is None:
            break

    assert len(pages) > 1
    assert [name for page in pages for name in page] == [f"lore-{index:02d}" for index in range(12)]


@pytest.mark.parametrize("count", [0, 3])
def test_prime_applicable_lore_rejects_out_of_range_cursor(tmp_path: Path, count: int) -> None:
    _many_lore(tmp_path, count)

    with pytest.raises(budget.InvalidCursorError):
        mcp_prime.prime_applicable_lore("goblin-ambush", cursor="99")
    with pytest.raises(budget.InvalidCursorError):
        mcp_prime.prime_applicable_lore("goblin-ambush", cursor="not-a-number")
