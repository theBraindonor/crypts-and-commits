import frontmatter
import pytest
from cac.core import boss, campaign, config, encounter, references, world


@pytest.fixture(autouse=True)
def setup_world(tmp_path):
    world.initialize_world(tmp_path)


def create(root, domain, name, *, parent="c001-work", archived=False):
    if domain == "boss":
        path = boss.create_boss(root, name, "Body", "Summary")
        destination = boss.boss_dir(root, archived=True) / path.name
    elif domain == "campaign":
        path = campaign.create_campaign(root, name, "Body")
        destination = campaign.archive_campaign_dir(root) / path.name
    else:
        if not campaign.exists(root, parent):
            campaign.create_campaign(root, parent, "Campaign")
        path = encounter.create_encounter(root, parent, name, "Body")
        destination = encounter.archive_encounter_dir(root, parent) / path.name
    if archived:
        post = frontmatter.load(path)
        post["archived"] = True
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
        destination.parent.mkdir(parents=True, exist_ok=True)
        path.rename(destination)
        return destination
    return path


@pytest.mark.parametrize("domain,prefix", [("boss", "b"), ("campaign", "c"), ("encounter", "e")])
@pytest.mark.parametrize("archived", [False, True])
def test_live_archive_full_short_and_padding(tmp_path, domain, prefix, archived):
    name = f"{prefix}001-goal"
    path = create(tmp_path, domain, name, archived=archived)
    before = path.read_bytes()
    inventory = references.Inventory(tmp_path)
    parent = "c001-work" if domain == "encounter" else None
    for value in (name, f"{prefix}001", f"{prefix}0001"):
        assert inventory.resolve(domain, value, parent) == name
    identity = inventory.identity(domain, name, parent)
    assert identity["canonical"] == name
    assert identity["short"] == ("c001/e001" if domain == "encounter" else f"{prefix}001")
    assert identity["reason"] is None
    assert path.read_bytes() == before


@pytest.mark.parametrize("domain,prefix", [("boss", "b"), ("campaign", "c"), ("encounter", "e")])
def test_numeric_collisions_and_exact_inspection_route(tmp_path, domain, prefix):
    first = f"{prefix}001-first"
    second = f"{prefix}0001-second"
    create(tmp_path, domain, first)
    create(tmp_path, domain, second, archived=True)
    parent = "c001-work" if domain == "encounter" else None
    inventory = references.Inventory(tmp_path)
    with pytest.raises(references.ReferenceError, match="Ambiguous"):
        inventory.resolve(domain, f"{prefix}001", parent)
    assert inventory.resolve(domain, first, parent) == first
    assert inventory.identity(domain, first, parent)["reason"] == "ambiguous"


@pytest.mark.parametrize("domain,prefix", [("boss", "b"), ("campaign", "c"), ("encounter", "e")])
@pytest.mark.parametrize("archived", [False, True])
def test_exact_short_shaped_name_wins_over_numbered_sibling(tmp_path, domain, prefix, archived):
    parent = "c001-work" if domain == "encounter" else None
    literal, numbered = f"{prefix}001", f"{prefix}001-slug"
    create(tmp_path, domain, literal, archived=archived)
    create(tmp_path, domain, numbered)
    inventory = references.Inventory(tmp_path)
    # The literal record is reachable and owns the short ref; its sibling keeps its full name.
    assert inventory.resolve(domain, literal, parent) == literal
    assert inventory.resolve(domain, numbered, parent) == numbered
    assert inventory.identity(domain, literal, parent)["short"] is not None
    assert inventory.identity(domain, numbered, parent) | {"short": None, "reason": "ambiguous"} == (
        inventory.identity(domain, numbered, parent)
    )
    with pytest.raises(references.AmbiguousReferenceError):
        inventory.resolve(domain, f"{prefix}0001", parent)


def test_numbered_siblings_without_exact_match_stay_ambiguous(tmp_path):
    create(tmp_path, "boss", "b001-one")
    create(tmp_path, "boss", "b001-two")
    with pytest.raises(references.AmbiguousReferenceError):
        references.Inventory(tmp_path).resolve("boss", "b001")


def test_qualified_ref_uses_exact_names_in_both_parts(tmp_path):
    create(tmp_path, "campaign", "c001")
    create(tmp_path, "campaign", "c001-other")
    create(tmp_path, "encounter", "e001", parent="c001")
    create(tmp_path, "encounter", "e001-task", parent="c001")
    assert references.Inventory(tmp_path).encounter("c001/e001", None) == ("c001", "e001")


def test_wrong_domain_shaped_literal_name_is_reachable(tmp_path):
    create(tmp_path, "campaign", "b001")
    assert references.Inventory(tmp_path).resolve("campaign", "b001") == "b001"


def test_duplicate_canonical_live_archive_fails(tmp_path):
    live = create(tmp_path, "campaign", "c001-work")
    archived = campaign.archive_campaign_dir(tmp_path) / live.name
    archived.parent.mkdir(parents=True)
    archived.write_bytes(live.read_bytes())
    with pytest.raises(references.ReferenceError, match="live/archive"):
        references.Inventory(tmp_path).resolve("campaign", "c001-work")


def test_qualified_context_and_no_active_campaign(tmp_path):
    create(tmp_path, "encounter", "e001-first", parent="c001-first")
    create(tmp_path, "encounter", "e001-second", parent="c002-second")
    inventory = references.Inventory(tmp_path)
    assert inventory.encounter("c001/e001", None) == ("c001-first", "e001-first")
    campaign.open_campaign(tmp_path, "c002-second")
    assert inventory.encounter("c001/e001", None) == ("c001-first", "e001-first")
    assert inventory.encounter("e001", None) == ("c002-second", "e001-second")
    assert inventory.encounter("c001/e001", "c001") == ("c001-first", "e001-first")
    with pytest.raises(references.ReferenceError, match="conflicts"):
        inventory.encounter("c001/e001", "c002")


@pytest.mark.parametrize(
    "value", ["c001/e001/extra", "../escape", "c001\\e001", "b001/e001", "c001/b001", "c001/", "/e001"]
)
def test_bad_qualified_refs_fail(tmp_path, value):
    create(tmp_path, "encounter", "e001-first")
    with pytest.raises((references.ReferenceError, FileNotFoundError)):
        references.Inventory(tmp_path).encounter(value, None)


def test_wrong_domain_unknown_and_no_context(tmp_path):
    create(tmp_path, "boss", "b1000-goal")
    assert references.Inventory(tmp_path).resolve("boss", "b1000") == "b1000-goal"
    with pytest.raises(references.ReferenceError):
        references.Inventory(tmp_path).resolve("boss", "c001")
    with pytest.raises(FileNotFoundError):
        references.Inventory(tmp_path).resolve("boss", "b999")
    with pytest.raises(campaign.NoActiveCampaignError):
        references.Inventory(tmp_path).encounter("e001", None)


def test_create_is_literal_and_dependencies_are_canonical(tmp_path):
    create(tmp_path, "boss", "b001-goal")
    create(tmp_path, "boss", "b002-other")
    assert references.select(tmp_path, "boss", "b001", create=True).name == "b001"
    selected = references.select(tmp_path, "boss", "b001", dependency="b002")
    assert selected.name == "b001-goal" and selected.dependency == "b002-other"
    assert (
        references.select(tmp_path, "boss", "b001", dependency="missing-canonical", remove=True).dependency
        == "missing-canonical"
    )
    create(tmp_path, "encounter", "e001-first", parent="c001-work")
    create(tmp_path, "encounter", "e001-second", parent="c002-work")
    with pytest.raises(references.ReferenceError):
        references.select(tmp_path, "encounter", "c001/e001", dependency="c002/e001")


def test_identity_unavailable_and_list_budgeting(tmp_path, monkeypatch):
    create(tmp_path, "campaign", "legacy")
    create(tmp_path, "encounter", "e001-work", parent="legacy")
    identity = references.Inventory(tmp_path).identity("encounter", "e001-work", "legacy")
    assert identity["short"] is None and identity["reason"] == "campaign_unnumbered"
    for name in ("b001-first", "b002-second", "old-goal"):
        create(tmp_path, "boss", name)
    names = boss.list_bosses(tmp_path)
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 220)
    cursor, gathered = None, []
    while True:
        page = references.identity_page(tmp_path, "boss", names, cursor)
        assert len(references.encoded(page)) <= 220
        assert [entry["canonical"] for entry in page["identities"]] == page["items"]
        gathered.extend(page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert gathered == names
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 2)
    with pytest.raises(references.ReferenceError, match="budget"):
        references.identity_page(tmp_path, "boss", names, None)


def test_missing_stored_canonical_edge_is_not_reinterpreted(tmp_path):
    create(tmp_path, "boss", "b001-real")
    path = create(tmp_path, "boss", "b002-dependent")
    post = frontmatter.load(path)
    post["depends_on"] = ["b001"]
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    with pytest.raises(boss.BossError, match="missing prerequisite"):
        boss.assign_dependency(tmp_path, "b002-dependent", "b001-real")
    assert boss.read_metadata(tmp_path, "b002-dependent")[0]["depends_on"] == ["b001"]
