import frontmatter
import pytest
from cac.core import campaign, config, encounter, references, ruling, search_index, world


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c002-rulings", "Tactics")
    encounter.create_encounter(tmp_path, "c002-rulings", "e001-core", "Plan")
    campaign.open_campaign(tmp_path, "c002-rulings")


def create(root, name="c002-e001-slugs-unique", body="[decision] café 🐉", summary="Summary", origin="GM"):
    return ruling.create_ruling(root, name, body, summary, origin)


def metadata(root, name="c002-e001-slugs-unique"):
    return ruling.read_metadata(root, name)[0]


# Naming and capture


def test_create_in_open_campaign_with_encounter(tmp_path):
    path = create(tmp_path)
    assert path == tmp_path / ".sourcebook" / "rulings" / "c002-e001-slugs-unique.md"
    meta, body = ruling.read_metadata(tmp_path, "c002-e001-slugs-unique")
    assert body == "[decision] café 🐉"
    assert meta["status"] == "recorded" and meta["archived"] is False
    assert meta["campaign"] == "c002-rulings" and meta["encounter"] == "e001-core"
    assert meta["summary"] == "Summary" and meta["origin"] == "GM"
    assert meta["resolution"] is None and meta["history"] == []
    assert meta["created_by"] == "John Hoff"


def test_e000_records_a_campaign_level_ruling(tmp_path):
    create(tmp_path, "c002-e000-scope")
    assert metadata(tmp_path, "c002-e000-scope")["encounter"] is None


def test_template_body_has_decision_context_consequences_headings():
    body = ruling.template_body()
    assert [line for line in body.splitlines() if line.startswith("## ")] == [
        "## Decision",
        "## Context",
        "## Consequences",
    ]


def test_encounter_in_any_status_qualifies(tmp_path):
    encounter.abandon_encounter(tmp_path, "c002-rulings", "e001-core", "Dropped")
    create(tmp_path)
    assert metadata(tmp_path)["encounter"] == "e001-core"


def test_multiple_rulings_per_encounter_need_unique_slugs(tmp_path):
    create(tmp_path, "c002-e001-one")
    create(tmp_path, "c002-e001-two")
    assert ruling.list_rulings(tmp_path) == ["c002-e001-one", "c002-e001-two"]


def _close(root, target):
    if target == "paused":
        campaign.pause_campaign(root, "c002-rulings")
    elif target == "completed":
        campaign.complete_campaign(root, "c002-rulings", "Done")
    elif target == "abandoned":
        campaign.abandon_campaign(root, "c002-rulings", "Dropped")


@pytest.mark.parametrize("target", ["paused", "completed", "abandoned"])
def test_create_refuses_campaigns_that_are_not_open(tmp_path, target):
    _close(tmp_path, target)
    with pytest.raises(ruling.RulingError, match="rumor"):
        create(tmp_path)
    assert not ruling.ruling_dir(tmp_path).exists()


def test_create_refuses_draft_campaign(tmp_path):
    campaign.create_campaign(tmp_path, "c003-next", "Tactics")
    with pytest.raises(ruling.RulingError, match="'draft'"):
        create(tmp_path, "c003-e000-early")


def test_create_succeeds_in_reactivated_campaign(tmp_path):
    campaign.complete_campaign(tmp_path, "c002-rulings", "Done")
    campaign.reactivate_campaign(tmp_path, "c002-rulings", "Review fixes")
    create(tmp_path)
    assert metadata(tmp_path)["status"] == "recorded"


def test_create_refuses_missing_campaign_or_encounter(tmp_path):
    with pytest.raises(campaign.CampaignNotFoundError):
        create(tmp_path, "c009-e000-nowhere")
    with pytest.raises(encounter.EncounterNotFoundError):
        create(tmp_path, "c002-e009-nowhere")
    assert not ruling.ruling_dir(tmp_path).exists()


@pytest.mark.parametrize(
    "name", ["", "r001-idea", "c002-slug", "c02-e001-x", "c002-e01-x", "c002-e001-", "c000-e000-x", "c002-e001-a/b"]
)
def test_malformed_names_are_refused(tmp_path, name):
    with pytest.raises(ruling.RulingError):
        create(tmp_path, name)
    assert not ruling.ruling_dir(tmp_path).exists()


def test_duplicate_names_are_refused_live_or_archived(tmp_path):
    create(tmp_path)
    with pytest.raises(ruling.RulingAlreadyExistsError):
        create(tmp_path)
    ruling.note(tmp_path, "c002-e001-slugs-unique", "Local detail")
    ruling.archive_ruling(tmp_path, "c002-e001-slugs-unique")
    with pytest.raises(ruling.RulingAlreadyExistsError):
        create(tmp_path)


@pytest.mark.parametrize(("summary", "origin"), [("", "O"), (" ", "O"), ("S", ""), ("S", " \n"), ("x" * 501, "O")])
def test_create_requires_summary_and_origin(tmp_path, summary, origin):
    with pytest.raises(ValueError):
        create(tmp_path, summary=summary, origin=origin)
    assert not ruling.ruling_dir(tmp_path).exists()


# Lifecycle


def test_update_replaces_fields_only_while_recorded(tmp_path):
    create(tmp_path)
    ruling.update_ruling(tmp_path, "c002-e001-slugs-unique", "New", "New summary", "Review")
    meta, body = ruling.read_metadata(tmp_path, "c002-e001-slugs-unique")
    assert (body, meta["summary"], meta["origin"]) == ("New", "New summary", "Review")
    ruling.canonize(tmp_path, "c002-e001-slugs-unique", "Added lore")
    path = ruling.ruling_path(tmp_path, "c002-e001-slugs-unique")
    before = path.read_bytes()
    with pytest.raises(ruling.RulingError, match="recorded"):
        ruling.update_ruling(tmp_path, "c002-e001-slugs-unique", "Body", "Summary", "Origin")
    assert path.read_bytes() == before


@pytest.mark.parametrize(("operation", "status"), [(ruling.canonize, "canonized"), (ruling.note, "noted")])
def test_dispositions_store_narrative_as_resolution_and_history(tmp_path, operation, status):
    create(tmp_path)
    operation(tmp_path, "c002-e001-slugs-unique", "Narrative")
    meta = metadata(tmp_path)
    assert meta["status"] == status and meta["resolution"] == "Narrative"
    action = "canonize" if status == "canonized" else "note"
    assert meta["history"] == [{"action": action, "message": "Narrative", "by": "John Hoff", "on": meta["updated_on"]}]


@pytest.mark.parametrize("operation", [ruling.canonize, ruling.note, ruling.reopen])
@pytest.mark.parametrize("message", ["", "  ", None])
def test_narratives_are_required(tmp_path, operation, message):
    create(tmp_path)
    if operation is ruling.reopen:
        ruling.note(tmp_path, "c002-e001-slugs-unique", "Detail")
    with pytest.raises(ruling.RulingError, match="nonblank"):
        operation(tmp_path, "c002-e001-slugs-unique", message)


def test_dispositions_require_recorded(tmp_path):
    create(tmp_path)
    ruling.canonize(tmp_path, "c002-e001-slugs-unique", "Lore")
    for operation in (ruling.canonize, ruling.note):
        with pytest.raises(ruling.RulingError, match="recorded"):
            operation(tmp_path, "c002-e001-slugs-unique", "Again")


def test_reopen_clears_resolution_and_appends_history(tmp_path):
    create(tmp_path)
    ruling.note(tmp_path, "c002-e001-slugs-unique", "Detail")
    ruling.reopen(tmp_path, "c002-e001-slugs-unique", "Turned out important")
    meta = metadata(tmp_path)
    assert meta["status"] == "recorded" and meta["resolution"] is None
    assert [entry["action"] for entry in meta["history"]] == ["note", "reopen"]
    with pytest.raises(ruling.RulingError):
        ruling.reopen(tmp_path, "c002-e001-slugs-unique", "Already recorded")


def test_archive_moves_resolved_rulings_and_leaves_campaign_untouched(tmp_path):
    campaign_path = campaign.campaign_path(tmp_path, "c002-rulings")
    create(tmp_path)
    with pytest.raises(ruling.RulingError):
        ruling.archive_ruling(tmp_path, "c002-e001-slugs-unique")
    before = campaign_path.read_bytes()
    ruling.canonize(tmp_path, "c002-e001-slugs-unique", "Lore")
    destination = ruling.archive_ruling(tmp_path, "c002-e001-slugs-unique")
    assert destination == tmp_path / ".sourcebook" / "archive" / "rulings" / "c002-e001-slugs-unique.md"
    assert not (tmp_path / ".sourcebook" / "rulings" / "c002-e001-slugs-unique.md").exists()
    assert metadata(tmp_path)["archived"] is True
    assert campaign_path.read_bytes() == before
    for operation in (ruling.reopen, ruling.canonize):
        with pytest.raises(ruling.RulingError):
            operation(tmp_path, "c002-e001-slugs-unique", "Message")
    with pytest.raises(ruling.RulingError):
        ruling.archive_ruling(tmp_path, "c002-e001-slugs-unique")


def test_list_filters_status_and_includes_archived(tmp_path):
    create(tmp_path, "c002-e001-a")
    create(tmp_path, "c002-e001-b")
    create(tmp_path, "c002-e000-c")
    ruling.note(tmp_path, "c002-e001-b", "Detail")
    ruling.canonize(tmp_path, "c002-e000-c", "Lore")
    ruling.archive_ruling(tmp_path, "c002-e000-c")
    assert ruling.list_rulings(tmp_path) == ["c002-e001-a", "c002-e001-b"]
    assert ruling.list_rulings(tmp_path, status="noted") == ["c002-e001-b"]
    assert ruling.list_rulings(tmp_path, include_archived=True, status="canonized") == ["c002-e000-c"]
    with pytest.raises(ruling.RulingError, match="Unknown ruling status"):
        ruling.list_rulings(tmp_path, status="open")


def test_list_refuses_live_archive_overlap(tmp_path):
    path = create(tmp_path)
    archived = ruling.ruling_dir(tmp_path, archived=True) / path.name
    archived.parent.mkdir(parents=True)
    archived.write_bytes(path.read_bytes())
    with pytest.raises(ruling.RulingError, match="Ambiguous"):
        ruling.list_rulings(tmp_path, include_archived=True)


def test_there_is_no_delete():
    assert not [name for name in dir(ruling) if "delete" in name]


# Campaign independence


def test_dispositions_continue_after_campaign_completion(tmp_path):
    create(tmp_path, "c002-e001-a")
    create(tmp_path, "c002-e001-b")
    campaign.complete_campaign(tmp_path, "c002-rulings", "Done")
    ruling.update_ruling(tmp_path, "c002-e001-a", "Hindsight", "Summary", "Planning")
    ruling.canonize(tmp_path, "c002-e001-a", "Lore updated")
    ruling.note(tmp_path, "c002-e001-b", "Local")
    ruling.archive_ruling(tmp_path, "c002-e001-b")
    assert metadata(tmp_path, "c002-e001-a")["status"] == "canonized"


def test_rulings_stay_valid_after_campaign_and_encounter_archival(tmp_path):
    create(tmp_path)
    encounter.abandon_encounter(tmp_path, "c002-rulings", "e001-core", "Dropped")
    campaign.complete_campaign(tmp_path, "c002-rulings", "Done")
    campaign.archive_campaign(tmp_path, "c002-rulings")
    meta = metadata(tmp_path)
    assert (meta["campaign"], meta["encounter"]) == ("c002-rulings", "e001-core")
    ruling.note(tmp_path, "c002-e001-slugs-unique", "Local")


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("campaign", "c003-other"),
        ("encounter", "e002-other"),
        ("encounter", None),
        ("status", "open"),
        ("resolution", "Premature"),
        ("archived", "no"),
        ("history", [{"action": "note"}]),
    ],
)
def test_load_rejects_inconsistent_metadata(tmp_path, key, value):
    path = create(tmp_path)
    post = frontmatter.load(path)
    post[key] = value
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    with pytest.raises(ruling.RulingError):
        ruling.read_metadata(tmp_path, "c002-e001-slugs-unique")


def test_load_rejects_resolved_status_without_resolution(tmp_path):
    path = create(tmp_path)
    post = frontmatter.load(path)
    post["status"] = "noted"
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    with pytest.raises(ruling.RulingError, match="resolution"):
        ruling.read_metadata(tmp_path, "c002-e001-slugs-unique")


# References


def test_ruling_names_are_canonical_only_and_never_campaign_refs(tmp_path):
    create(tmp_path)
    inventory = references.Inventory(tmp_path)
    assert inventory.resolve("ruling", "c002-e001-slugs-unique") == "c002-e001-slugs-unique"
    for value in ("c002", "c002-e001", "e001"):
        with pytest.raises(FileNotFoundError):
            inventory.resolve("ruling", value)
    assert inventory.identity("ruling", "c002-e001-slugs-unique") == {
        "canonical": "c002-e001-slugs-unique",
        "short": None,
        "reason": "canonical_only",
    }
    assert inventory.numeric["ruling", None] == {}
    # The ruling's own name is never matched against campaign storage.
    assert inventory.resolve("campaign", "c002") == "c002-rulings"
    assert "c002-e001-slugs-unique" not in inventory.names("campaign")
    with pytest.raises(campaign.CampaignNotFoundError):
        inventory.resolve("campaign", "c002-e001-slugs-unique")


def test_ruling_name_pattern_is_disjoint_from_short_refs():
    assert config.SHORT_REFERENCE_PATTERN.fullmatch("c002-e001-x") is None
    assert config.RULING_NAME_PATTERN.fullmatch("c002") is None


# Index isolation


def test_ruling_writes_leave_the_index_fresh_and_unchanged(tmp_path):
    search_index.rebuild_index(tmp_path)
    counts = search_index.index_counts(tmp_path)
    create(tmp_path, "c002-e001-a", body="zebraphrase")
    ruling.update_ruling(tmp_path, "c002-e001-a", "zebraphrase two", "Summary", "GM")
    ruling.canonize(tmp_path, "c002-e001-a", "Lore")
    ruling.archive_ruling(tmp_path, "c002-e001-a")
    assert search_index.status(tmp_path)["freshness"] == "fresh"
    assert search_index.index_counts(tmp_path) == counts
    assert search_index.search(tmp_path, "zebraphrase", include_archived=True) == []
