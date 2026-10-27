import pytest
from cac.core import campaign, encounter, references, search_index, world


def history(root):
    world.initialize_world(root)
    campaign.create_campaign(root, "c999-old", "Old")
    for name in ("e999-old", "e1000-latest"):
        encounter.create_encounter(root, "c999-old", name, "Old")
        encounter.abandon_encounter(root, "c999-old", name, "Historical")
    campaign.abandon_campaign(root, "c999-old", "Historical")
    campaign.archive_campaign(root, "c999-old")
    campaign.create_campaign(root, "c001-live", "Live")
    encounter.create_encounter(root, "c001-live", "e001-live", "Live")


@pytest.mark.parametrize("index", ["missing", "fresh", "stale"])
def test_retained_allocation_inventory_is_complete_and_read_only(tmp_path, index):
    history(tmp_path)
    if index != "missing":
        search_index.rebuild_index(tmp_path)
    if index == "stale":
        path = world.world_path(tmp_path)
        path.write_bytes(path.read_bytes() + b"\nExternal change\n")
    before = {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert campaign.list_campaigns_with_status(tmp_path) == [("c001-live", "draft")]
    assert campaign.list_campaigns_with_status(tmp_path, include_archived=True) == [
        ("c001-live", "draft"),
        ("c999-old", "abandoned"),
    ]
    assert encounter.list_encounters(tmp_path, "c999-old") == []
    names = encounter.list_encounters(tmp_path, "c999-old", include_archived=True)
    assert set(names) == {"e999-old", "e1000-latest"}
    assert max(int(name.split("-")[0][1:]) for name in names) + 1 == 1001
    assert encounter.list_encounters(tmp_path, "c001-live", include_archived=True) == ["e001-live"]
    assert {str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("domain", ["campaign", "encounter"])
def test_duplicate_live_archive_identity_is_rejected(tmp_path, domain):
    history(tmp_path)
    if domain == "campaign":
        source = campaign.campaign_path(tmp_path, "c999-old")
        target = campaign.campaign_dir(tmp_path) / source.name
        operation = lambda: campaign.list_campaigns_with_status(tmp_path, include_archived=True)
    else:
        source = encounter.encounter_path(tmp_path, "c999-old", "e999-old")
        target = encounter.encounter_dir(tmp_path, "c999-old") / source.name
        operation = lambda: encounter.list_encounters(tmp_path, "c999-old", include_archived=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    with pytest.raises(references.AmbiguousReferenceError, match="Ambiguous"):
        operation()


@pytest.mark.parametrize("domain", ["campaign", "encounter"])
def test_archive_namespace_collision_is_rejected(tmp_path, domain):
    world.initialize_world(tmp_path)
    directory = (
        campaign.archive_campaign_dir(tmp_path)
        if domain == "campaign"
        else encounter.archive_encounter_dir(tmp_path, "c001-empty")
    )
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.write_text("Not a directory", encoding="utf-8")
    with pytest.raises(ValueError, match="directory"):
        if domain == "campaign":
            campaign.list_campaigns_with_status(tmp_path, include_archived=True)
        else:
            encounter.list_encounters(tmp_path, "c001-empty", include_archived=True)


def test_empty_archive_inventories_create_nothing(tmp_path):
    assert campaign.list_campaigns_with_status(tmp_path, include_archived=True) == []
    assert encounter.list_encounters(tmp_path, "c001-empty", include_archived=True) == []
    assert list(tmp_path.iterdir()) == []
