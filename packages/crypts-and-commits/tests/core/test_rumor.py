import frontmatter
import pytest
from cac.core import boss, campaign, config, frontmatter_utils, references, rumor, search_index, world


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)


def create(root, name="r001-idea", body="[notes] café 🐉", summary="Summary", origin="Standup"):
    return rumor.create_rumor(root, name, body, summary, origin)


def goal(root, name="b001-goal", *, available=False):
    boss.create_boss(root, name, "Goal", "Summary")
    if available:
        boss.make_available(root, name)
    return boss.boss_path(root, name)


def metadata(root, name="r001-idea"):
    return rumor.read_metadata(root, name)[0]


def test_create_stores_fields_at_the_root_rumors_directory(tmp_path):
    path = create(tmp_path)
    assert path == tmp_path / ".sourcebook" / "rumors" / "r001-idea.md"
    assert not (tmp_path / ".sourcebook" / "bosses" / "rumors").exists()
    meta, body = rumor.read_metadata(tmp_path, "r001-idea")
    assert body == "[notes] café 🐉"
    assert meta["status"] == "open"
    assert meta["origin"] == "Standup"
    assert meta["summary"] == "Summary"
    assert meta["boss"] is None and meta["resolution"] is None
    assert meta["history"] == [] and meta["archived"] is False
    assert meta["created_by"] == "John Hoff"


def test_empty_body_is_allowed(tmp_path):
    create(tmp_path, body="")
    assert rumor.read_metadata(tmp_path, "r001-idea")[1] == ""


@pytest.mark.parametrize(
    ("summary", "origin"), [("", "Origin"), ("  ", "Origin"), ("Summary", ""), ("Summary", " \n"), ("x" * 501, "O")]
)
def test_create_requires_summary_and_origin(tmp_path, summary, origin):
    with pytest.raises(ValueError):
        create(tmp_path, summary=summary, origin=origin)
    assert not rumor.rumor_dir(tmp_path).exists()


def test_origin_is_free_text_not_a_repository_reference(tmp_path):
    create(tmp_path, origin="c999/e999 and a customer call")
    assert metadata(tmp_path)["origin"] == "c999/e999 and a customer call"


@pytest.mark.parametrize("name", [".", "..", "../escape", "a/b", ""])
def test_invalid_names_do_not_create_storage(tmp_path, name):
    with pytest.raises(rumor.RumorError):
        create(tmp_path, name=name)
    assert not rumor.rumor_dir(tmp_path).exists()


def test_duplicate_names_are_rejected_live_or_archived(tmp_path):
    create(tmp_path)
    with pytest.raises(rumor.RumorAlreadyExistsError):
        create(tmp_path)
    rumor.dismiss(tmp_path, "r001-idea", "No")
    rumor.archive_rumor(tmp_path, "r001-idea")
    with pytest.raises(rumor.RumorAlreadyExistsError):
        create(tmp_path)


def test_similar_rumors_are_never_deduplicated(tmp_path):
    create(tmp_path, "r001-faster-ci")
    create(tmp_path, "r002-faster-ci")
    assert rumor.list_rumors(tmp_path) == ["r001-faster-ci", "r002-faster-ci"]


def test_update_is_a_full_replacement_only_while_open(tmp_path):
    create(tmp_path)
    rumor.update_rumor(tmp_path, "r001-idea", "New body", "New summary", "New origin")
    meta, body = rumor.read_metadata(tmp_path, "r001-idea")
    assert (body, meta["summary"], meta["origin"]) == ("New body", "New summary", "New origin")
    with pytest.raises(ValueError):
        rumor.update_rumor(tmp_path, "r001-idea", "Body", "Summary", "")
    rumor.dismiss(tmp_path, "r001-idea", "No")
    before = rumor.rumor_path(tmp_path, "r001-idea").read_bytes()
    with pytest.raises(rumor.RumorError, match="open"):
        rumor.update_rumor(tmp_path, "r001-idea", "Body", "Summary", "Origin")
    assert rumor.rumor_path(tmp_path, "r001-idea").read_bytes() == before


@pytest.mark.parametrize("message", [None, "", "Matches the goal"])
def test_promote_links_only_the_rumor_and_accepts_short_boss_refs(tmp_path, message):
    boss_path = goal(tmp_path)
    before = boss_path.read_bytes()
    create(tmp_path)
    rumor.promote(tmp_path, "r001-idea", "b001", message)
    meta = metadata(tmp_path)
    assert meta["status"] == "promoted" and meta["boss"] == "b001-goal"
    assert meta["resolution"] == (message or None)
    assert meta["history"] == [
        {"action": "promote", "message": message or None, "by": "John Hoff", "on": meta["updated_on"]}
    ]
    assert boss_path.read_bytes() == before


def test_many_rumors_may_promote_to_one_boss(tmp_path):
    boss_path = goal(tmp_path, available=True)
    before = boss_path.read_bytes()
    for name in ("r001-one", "r002-two", "r003-three"):
        create(tmp_path, name)
        rumor.promote(tmp_path, name, "b001-goal")
    assert rumor.list_rumors(tmp_path, status="promoted") == ["r001-one", "r002-two", "r003-three"]
    assert boss_path.read_bytes() == before


@pytest.mark.parametrize("state", ["assigned", "withdrawn", "vanquished", "archived"])
def test_promote_refuses_bosses_that_are_not_unassigned_proposed_or_available(tmp_path, state):
    goal(tmp_path, available=True)
    if state == "assigned":
        boss.assign_campaign(tmp_path, "b001-goal", "c001-work", "Tactics")
    elif state in ("withdrawn", "archived"):
        boss.withdraw(tmp_path, "b001-goal")
        if state == "archived":
            boss.archive_boss(tmp_path, "b001-goal")
    else:
        boss.assign_campaign(tmp_path, "b001-goal", "c001-work", "Tactics")
        campaign.open_campaign(tmp_path, "c001-work")
        campaign.complete_campaign(tmp_path, "c001-work", "Done")
    path = create(tmp_path)
    before = path.read_bytes()
    with pytest.raises(rumor.RumorError, match="unassigned"):
        rumor.promote(tmp_path, "r001-idea", "b001-goal")
    assert path.read_bytes() == before


def test_promote_refuses_missing_bosses_and_non_open_rumors(tmp_path):
    create(tmp_path)
    with pytest.raises(boss.BossNotFoundError):
        rumor.promote(tmp_path, "r001-idea", "b404")
    goal(tmp_path)
    rumor.dismiss(tmp_path, "r001-idea", "No")
    with pytest.raises(rumor.RumorError, match="open"):
        rumor.promote(tmp_path, "r001-idea", "b001-goal")


@pytest.mark.parametrize("message", [None, "", "  "])
def test_dismiss_and_reopen_require_messages(tmp_path, message):
    create(tmp_path)
    with pytest.raises(rumor.RumorError, match="dismissal reason"):
        rumor.dismiss(tmp_path, "r001-idea", message)
    rumor.dismiss(tmp_path, "r001-idea", "Out of scope")
    with pytest.raises(rumor.RumorError, match="reopen message"):
        rumor.reopen(tmp_path, "r001-idea", message)


def test_reopen_clears_link_and_keeps_history(tmp_path):
    goal(tmp_path)
    create(tmp_path)
    rumor.promote(tmp_path, "r001-idea", "b001-goal", "Linked")
    rumor.reopen(tmp_path, "r001-idea", "Wrong goal")
    meta = metadata(tmp_path)
    assert meta["status"] == "open" and meta["boss"] is None and meta["resolution"] is None
    rumor.update_rumor(tmp_path, "r001-idea", "Edited", "Summary", "Origin")
    rumor.dismiss(tmp_path, "r001-idea", "Not now")
    actions = [(entry["action"], entry["message"]) for entry in metadata(tmp_path)["history"]]
    assert actions == [("promote", "Linked"), ("reopen", "Wrong goal"), ("dismiss", "Not now")]
    assert metadata(tmp_path)["resolution"] == "Not now"


def test_reopen_refuses_open_rumors(tmp_path):
    create(tmp_path)
    with pytest.raises(rumor.RumorError):
        rumor.reopen(tmp_path, "r001-idea", "Already open")


def test_archive_requires_a_resolved_rumor_and_keeps_it_readable(tmp_path):
    path = create(tmp_path)
    with pytest.raises(rumor.RumorError, match="open"):
        rumor.archive_rumor(tmp_path, "r001-idea")
    rumor.dismiss(tmp_path, "r001-idea", "No")
    destination = rumor.archive_rumor(tmp_path, "r001-idea")
    assert destination == rumor.rumor_dir(tmp_path, archived=True) / "r001-idea.md"
    assert not path.exists()
    assert metadata(tmp_path)["archived"] is True
    assert rumor.list_rumors(tmp_path) == []
    assert rumor.list_rumors(tmp_path, include_archived=True) == ["r001-idea"]
    for operation in (
        lambda: rumor.reopen(tmp_path, "r001-idea", "Back"),
        lambda: rumor.archive_rumor(tmp_path, "r001-idea"),
        lambda: rumor.update_rumor(tmp_path, "r001-idea", "B", "S", "O"),
    ):
        with pytest.raises(rumor.RumorError):
            operation()


@pytest.mark.parametrize("dismissed", [False, True])
def test_renumber_open_and_dismissed_rumors(tmp_path, dismissed):
    create(tmp_path)
    if dismissed:
        rumor.dismiss(tmp_path, "r001-idea", "No")
    before = metadata(tmp_path)
    old = rumor.rumor_path(tmp_path, "r001-idea")
    new = rumor.renumber(tmp_path, "r001-idea", "r002-idea")
    assert not old.exists() and new == rumor.rumor_dir(tmp_path) / "r002-idea.md"
    after = metadata(tmp_path, "r002-idea")
    assert after["name"] == "r002-idea"
    unchanged = {key for key in before if key not in ("name", "updated_by", "updated_on")}
    assert {key: after[key] for key in unchanged} == {key: before[key] for key in unchanged}
    assert rumor.read_metadata(tmp_path, "r002-idea")[1] == "[notes] café 🐉"


def test_renumber_refuses_promoted_archived_and_taken_names(tmp_path):
    goal(tmp_path)
    create(tmp_path)
    create(tmp_path, "r002-other")
    with pytest.raises(rumor.RumorAlreadyExistsError):
        rumor.renumber(tmp_path, "r001-idea", "r002-other")
    rumor.promote(tmp_path, "r001-idea", "b001-goal")
    with pytest.raises(rumor.RumorError, match="promoted"):
        rumor.renumber(tmp_path, "r001-idea", "r003-idea")
    rumor.reopen(tmp_path, "r001-idea", "Renumber first")
    rumor.renumber(tmp_path, "r001-idea", "r003-idea")
    rumor.dismiss(tmp_path, "r002-other", "No")
    rumor.archive_rumor(tmp_path, "r002-other")
    with pytest.raises(rumor.RumorError):
        rumor.renumber(tmp_path, "r002-other", "r004-other")
    with pytest.raises(rumor.RumorAlreadyExistsError):
        rumor.renumber(tmp_path, "r003-idea", "r002-other")


def test_list_status_filter_and_invalid_status(tmp_path):
    goal(tmp_path)
    for name in ("r001-a", "r002-b", "r003-c"):
        create(tmp_path, name)
    rumor.promote(tmp_path, "r001-a", "b001-goal")
    rumor.dismiss(tmp_path, "r002-b", "No")
    assert rumor.list_rumors(tmp_path, status="open") == ["r003-c"]
    assert rumor.list_rumors(tmp_path, status="dismissed") == ["r002-b"]
    rumor.archive_rumor(tmp_path, "r002-b")
    assert rumor.list_rumors(tmp_path, status="dismissed") == []
    assert rumor.list_rumors(tmp_path, include_archived=True, status="dismissed") == ["r002-b"]
    with pytest.raises(rumor.RumorError, match="Unknown rumor status"):
        rumor.list_rumors(tmp_path, status="closed")


def test_short_references_resolve_live_archived_and_reject_ambiguity(tmp_path):
    create(tmp_path)
    inventory = references.Inventory(tmp_path)
    assert inventory.resolve("rumor", "r001") == "r001-idea"
    assert inventory.identity("rumor", "r001-idea") == {"canonical": "r001-idea", "short": "r001", "reason": None}
    rumor.dismiss(tmp_path, "r001-idea", "No")
    rumor.archive_rumor(tmp_path, "r001-idea")
    assert references.Inventory(tmp_path).resolve("rumor", "r001") == "r001-idea"
    create(tmp_path, "r001-collision")
    with pytest.raises(references.AmbiguousReferenceError):
        references.Inventory(tmp_path).resolve("rumor", "r001")
    assert references.Inventory(tmp_path).resolve("rumor", "r001-collision") == "r001-collision"
    with pytest.raises(rumor.RumorNotFoundError):
        references.Inventory(tmp_path).resolve("rumor", "r404")
    with pytest.raises(references.ReferenceError):
        references.Inventory(tmp_path).resolve("rumor", "b001")


def test_create_names_stay_literal(tmp_path):
    create(tmp_path)
    path = create(tmp_path, "r001")
    assert path.name == "r001.md"
    assert references.Inventory(tmp_path).resolve("rumor", "r001") == "r001"


def test_index_rows_follow_every_write_and_stay_fresh(tmp_path):
    goal(tmp_path)
    search_index.rebuild_index(tmp_path)
    create(tmp_path, origin="customer-escalation")
    assert search_index.status(tmp_path)["freshness"] == "fresh"
    hits = search_index.search(tmp_path, "customer-escalation", object_type="rumor")
    assert [(hit.name, hit.status) for hit in hits] == [("r001-idea", "open")]
    rumor.renumber(tmp_path, "r001-idea", "r002-idea")
    rumor.promote(tmp_path, "r002-idea", "b001-goal")
    hits = search_index.search(tmp_path, "customer-escalation", object_type="rumor")
    assert [(hit.name, hit.status) for hit in hits] == [("r002-idea", "promoted")]
    rumor.reopen(tmp_path, "r002-idea", "Again")
    rumor.dismiss(tmp_path, "r002-idea", "No")
    rumor.archive_rumor(tmp_path, "r002-idea")
    assert search_index.search(tmp_path, "customer-escalation", object_type="rumor") == []
    archived = search_index.search(tmp_path, "customer-escalation", object_type="rumor", include_archived=True)
    assert [(hit.name, hit.archived) for hit in archived] == [("r002-idea", True)]
    assert search_index.status(tmp_path)["freshness"] == "fresh"
    assert search_index.rebuild_index(tmp_path) == search_index.rebuild_index(tmp_path)
    assert search_index.index_counts(tmp_path)["rumor"] == 1


def test_existing_index_without_rumors_stays_fresh(tmp_path):
    search_index.rebuild_index(tmp_path)
    assert search_index.status(tmp_path)["freshness"] == "fresh"
    assert "rumor" not in search_index.index_counts(tmp_path)


def test_failed_renumber_recovers_files_and_index(tmp_path, monkeypatch):
    search_index.rebuild_index(tmp_path)
    old = create(tmp_path)
    before = old.read_bytes()

    def fail(root, path):
        raise OSError("simulated failure")

    monkeypatch.setattr(frontmatter_utils, "delete_post", fail)
    with pytest.raises(OSError, match="simulated"):
        rumor.renumber(tmp_path, "r001-idea", "r002-idea")
    assert old.read_bytes() == before
    assert not (rumor.rumor_dir(tmp_path) / "r002-idea.md").exists()
    assert search_index.status(tmp_path)["freshness"] == "fresh"
    assert [hit.name for hit in search_index.search(tmp_path, "Standup", object_type="rumor")] == ["r001-idea"]


@pytest.mark.parametrize(
    "damage",
    [
        {"status": "closed"},
        {"name": "other"},
        {"archived": True},
        {"boss": "b001-goal"},
        {"history": [{"action": "promote"}]},
    ],
)
def test_inconsistent_metadata_is_rejected(tmp_path, damage):
    path = create(tmp_path)
    post = frontmatter.load(path)
    post.metadata.update(damage)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    with pytest.raises(rumor.RumorError):
        rumor.read_metadata(tmp_path, "r001-idea")


def test_requires_bootstrapped_world(tmp_path):
    world.world_path(tmp_path).unlink()
    with pytest.raises(world.WorldNotFoundError):
        create(tmp_path)


def test_rumor_statuses_and_directory_configuration():
    assert config.RUMOR_STATUSES == ("open", "promoted", "dismissed")
    assert config.RUMOR_DIR_NAME == "rumors"
    assert config.SEARCH_INDEX_OBJECT_TYPE_RUMOR in config.SEARCH_INDEX_OBJECT_TYPES
