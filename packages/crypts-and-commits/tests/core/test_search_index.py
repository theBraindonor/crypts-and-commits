import sqlite3
import threading
import time
from pathlib import Path

import frontmatter
import pytest
from cac.core import campaign, encounter, lore, region, search_index, world
from cac.core.paths import search_index_db_path


def _make_campaign(tmp_path: Path, name: str = "opening-gambit") -> None:
    campaign.create_campaign(tmp_path, name, "Body.")


def test_index_counts_returns_none_before_any_rebuild(tmp_path: Path) -> None:
    assert search_index.index_counts(tmp_path) is None


def test_index_counts_does_not_create_db_file(tmp_path: Path) -> None:
    search_index.index_counts(tmp_path)

    assert not search_index_db_path(tmp_path).exists()


def test_rebuild_index_indexes_encounters_across_campaigns(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "campaign-a")
    _make_campaign(tmp_path, "campaign-b")
    encounter.create_encounter(tmp_path, "campaign-a", "goblin-ambush", "Fight the goblins in the cave.")
    encounter.create_encounter(tmp_path, "campaign-b", "dragon-hoard", "Recover the dragon's hoard of gold.")

    count = search_index.rebuild_index(tmp_path)

    assert count == 4
    assert search_index.index_counts(tmp_path) == {"encounter": 2, "campaign": 2}


def test_rebuild_index_is_a_true_drop_and_reindex(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins.")
    search_index.rebuild_index(tmp_path)
    encounter.delete_encounter(tmp_path, "opening-gambit", "goblin-ambush")
    encounter.create_encounter(tmp_path, "opening-gambit", "dragon-hoard", "Recover the hoard.")

    count = search_index.rebuild_index(tmp_path)

    assert count == 2
    assert search_index.index_counts(tmp_path) == {"encounter": 1, "campaign": 1}


def test_rebuild_index_reflects_updated_body(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "original body text")
    search_index.rebuild_index(tmp_path)
    encounter.update_encounter(tmp_path, "opening-gambit", "goblin-ambush", "revised body text")

    search_index.rebuild_index(tmp_path)

    conn = sqlite3.connect(search_index_db_path(tmp_path))
    try:
        rows = conn.execute("SELECT body FROM sourcebook_fts WHERE sourcebook_fts MATCH 'revised'").fetchall()
        stale = conn.execute("SELECT body FROM sourcebook_fts WHERE sourcebook_fts MATCH 'original'").fetchall()
    finally:
        conn.close()
    assert len(rows) == 1
    assert stale == []


def test_index_visible_to_a_second_independent_connection(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "searchable ambush text")

    search_index.rebuild_index(tmp_path)

    other_conn = sqlite3.connect(search_index_db_path(tmp_path))
    try:
        rows = other_conn.execute("SELECT name FROM sourcebook_fts WHERE sourcebook_fts MATCH 'searchable'").fetchall()
    finally:
        other_conn.close()
    assert rows == [("goblin-ambush",)]


def test_search_returns_none_before_any_rebuild(tmp_path: Path) -> None:
    assert search_index.search(tmp_path, "goblins") is None


def test_search_returns_empty_list_for_no_match(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins in the cave.")
    search_index.rebuild_index(tmp_path)

    assert search_index.search(tmp_path, "dragons") == []


def test_search_finds_matching_encounter_with_full_metadata(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "campaign-a")
    _make_campaign(tmp_path, "campaign-b")
    encounter.create_encounter(tmp_path, "campaign-a", "goblin-ambush", "Fight the goblins in the cave.")
    encounter.create_encounter(tmp_path, "campaign-b", "dragon-hoard", "Recover the dragon's hoard of gold.")
    search_index.rebuild_index(tmp_path)

    hits = search_index.search(tmp_path, "goblins")

    assert len(hits) == 1
    hit = hits[0]
    assert hit.rank == 1
    assert hit.object_type == "encounter"
    assert hit.campaign == "campaign-a"
    assert hit.name == "goblin-ambush"
    assert hit.status == "draft"
    assert hit.updated_on
    assert "goblins" in hit.excerpt.lower()


def test_search_phrase_with_fts5_special_characters_does_not_raise(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", 'A test-driven "quote" and a hyphen.')
    search_index.rebuild_index(tmp_path)

    hits = search_index.search(tmp_path, 'test-driven "quote"')

    assert hits == [] or hits[0].name == "goblin-ambush"


def test_search_filters_by_object_type(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins in the cave.")
    search_index.rebuild_index(tmp_path)

    assert len(search_index.search(tmp_path, "goblins", object_type="encounter")) == 1


def test_search_unknown_object_type_raises(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    search_index.rebuild_index(tmp_path)

    with pytest.raises(search_index.InvalidSearchQueryError):
        search_index.search(tmp_path, "goblins", object_type="not-a-type")


def test_search_pages_with_limit_and_offset(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    for i in range(3):
        encounter.create_encounter(tmp_path, "opening-gambit", f"goblin-ambush-{i}", "Fight the goblins.")
    search_index.rebuild_index(tmp_path)

    first_page = search_index.search(tmp_path, "goblins", limit=2, offset=0)
    second_page = search_index.search(tmp_path, "goblins", limit=2, offset=2)

    assert [hit.rank for hit in first_page] == [1, 2]
    assert len(second_page) == 1
    assert second_page[0].rank == 3


def test_search_blank_phrase_raises(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    search_index.rebuild_index(tmp_path)

    with pytest.raises(search_index.EmptySearchPhraseError):
        search_index.search(tmp_path, "   ")


def test_search_invalid_limit_and_offset_raise(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    search_index.rebuild_index(tmp_path)

    with pytest.raises(search_index.InvalidSearchQueryError):
        search_index.search(tmp_path, "goblins", limit=0)
    with pytest.raises(search_index.InvalidSearchQueryError):
        search_index.search(tmp_path, "goblins", offset=-1)


def test_search_snippet_tokens_controls_excerpt_length(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    body = "goblins " + " ".join(f"word{i}" for i in range(40))
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", body)
    search_index.rebuild_index(tmp_path)

    short_hit = search_index.search(tmp_path, "goblins", snippet_tokens=1)[0]
    long_hit = search_index.search(tmp_path, "goblins", snippet_tokens=40)[0]

    assert len(short_hit.excerpt) < len(long_hit.excerpt)


def test_search_default_snippet_tokens_is_twenty(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    body = "goblins " + " ".join(f"word{i}" for i in range(40))
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", body)
    search_index.rebuild_index(tmp_path)

    default_hit = search_index.search(tmp_path, "goblins")[0]
    explicit_hit = search_index.search(tmp_path, "goblins", snippet_tokens=search_index.SEARCH_DEFAULT_SNIPPET_TOKENS)[
        0
    ]

    assert default_hit.excerpt == explicit_hit.excerpt


def test_search_invalid_snippet_tokens_raises(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    search_index.rebuild_index(tmp_path)

    with pytest.raises(search_index.InvalidSearchQueryError):
        search_index.search(tmp_path, "goblins", snippet_tokens=0)
    with pytest.raises(search_index.InvalidSearchQueryError):
        search_index.search(tmp_path, "goblins", snippet_tokens=65)


def test_rebuild_index_indexes_world_lore_and_region(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "clean-code", "Keep functions short.", "Summary.")
    region.create_region(tmp_path, "backend", "FastAPI service internals.", "Summary.")

    count = search_index.rebuild_index(tmp_path)

    assert count == 3
    assert search_index.index_counts(tmp_path) == {"world": 1, "lore": 1, "region": 1}


def test_rebuild_index_indexes_campaigns(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "campaign-a")
    _make_campaign(tmp_path, "campaign-b")

    count = search_index.rebuild_index(tmp_path)

    assert count == 2
    assert search_index.index_counts(tmp_path) == {"campaign": 2}


def test_index_counts_omits_world_when_not_bootstrapped(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins.")

    search_index.rebuild_index(tmp_path)

    assert search_index.index_counts(tmp_path) == {"encounter": 1, "campaign": 1}


def test_search_finds_matching_lore_with_enabled_status(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "clean-code", "Keep functions short and focused.", "Summary.")
    search_index.rebuild_index(tmp_path)

    hits = search_index.search(tmp_path, "functions", object_type="lore")

    assert len(hits) == 1
    hit = hits[0]
    assert hit.object_type == "lore"
    assert hit.campaign == ""
    assert hit.name == "clean-code"
    assert hit.status == "enabled"
    assert hit.updated_on
    assert "functions" in hit.excerpt.lower()


def test_search_finds_disabled_lore_labeled_disabled(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "clean-code", "Keep functions short and focused.", "Summary.")
    lore.set_enabled(tmp_path, "clean-code", False)
    search_index.rebuild_index(tmp_path)

    hits = search_index.search(tmp_path, "functions")

    assert len(hits) == 1
    assert hits[0].status == "disabled"


def test_search_finds_matching_region(tmp_path: Path) -> None:
    region.create_region(tmp_path, "backend", "FastAPI service internals live here.", "Summary.")
    search_index.rebuild_index(tmp_path)

    hits = search_index.search(tmp_path, "FastAPI", object_type="region")

    assert len(hits) == 1
    hit = hits[0]
    assert hit.object_type == "region"
    assert hit.campaign == ""
    assert hit.name == "backend"
    assert hit.status == ""
    assert hit.updated_on


def test_search_finds_matching_world(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    world.update_body(tmp_path, "This world is about distinctive-world-phrase content.")
    search_index.rebuild_index(tmp_path)

    hits = search_index.search(tmp_path, "distinctive-world-phrase", object_type="world")

    assert len(hits) == 1
    hit = hits[0]
    assert hit.object_type == "world"
    assert hit.campaign == ""
    assert hit.status == ""
    assert hit.updated_on


def test_search_finds_matching_campaign_with_full_metadata(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "This initiative covers distinctive-campaign-phrase work.")
    search_index.rebuild_index(tmp_path)

    hits = search_index.search(tmp_path, "distinctive-campaign-phrase", object_type="campaign")

    assert len(hits) == 1
    hit = hits[0]
    assert hit.object_type == "campaign"
    assert hit.campaign == ""
    assert hit.name == "opening-gambit"
    assert hit.status == "draft"
    assert hit.updated_on
    assert "distinctive-campaign-phrase" in hit.excerpt.lower()


# --- Incremental sync (create/update/delete without an intervening rebuild) ---


def test_create_encounter_after_rebuild_is_immediately_searchable(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    search_index.rebuild_index(tmp_path)

    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins in the cave.")

    hits = search_index.search(tmp_path, "goblins", object_type="encounter")
    assert len(hits) == 1
    assert hits[0].name == "goblin-ambush"


def test_update_encounter_after_rebuild_is_immediately_reflected(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "original body text")
    search_index.rebuild_index(tmp_path)

    encounter.update_encounter(tmp_path, "opening-gambit", "goblin-ambush", "revised body text")

    assert search_index.search(tmp_path, "revised")[0].name == "goblin-ambush"
    assert search_index.search(tmp_path, "original") == []
    assert search_index.index_counts(tmp_path) == {"encounter": 1, "campaign": 1}


def test_delete_encounter_after_rebuild_is_immediately_removed(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins.")
    search_index.rebuild_index(tmp_path)

    encounter.delete_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    assert search_index.search(tmp_path, "goblins") == []
    assert search_index.index_counts(tmp_path) == {"campaign": 1}


def test_create_lore_after_rebuild_is_immediately_searchable(tmp_path: Path) -> None:
    search_index.rebuild_index(tmp_path)

    lore.create_lore(tmp_path, "clean-code", "Keep functions short and focused.", "Summary.")

    hits = search_index.search(tmp_path, "functions", object_type="lore")
    assert len(hits) == 1
    assert hits[0].status == "enabled"


def test_update_lore_after_rebuild_is_immediately_reflected(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "clean-code", "original lore text", "Summary.")
    search_index.rebuild_index(tmp_path)

    lore.update_lore(tmp_path, "clean-code", "revised lore text", "Summary.")

    assert search_index.search(tmp_path, "revised")[0].name == "clean-code"
    assert search_index.search(tmp_path, "original") == []


def test_delete_lore_after_rebuild_is_immediately_removed(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "clean-code", "Keep functions short.", "Summary.")
    search_index.rebuild_index(tmp_path)

    lore.delete_lore(tmp_path, "clean-code")

    assert search_index.search(tmp_path, "functions") == []
    assert search_index.index_counts(tmp_path) == {}


def test_create_region_after_rebuild_is_immediately_searchable(tmp_path: Path) -> None:
    search_index.rebuild_index(tmp_path)

    region.create_region(tmp_path, "backend", "FastAPI service internals.", "Summary.")

    hits = search_index.search(tmp_path, "FastAPI", object_type="region")
    assert len(hits) == 1
    assert hits[0].name == "backend"


def test_delete_region_after_rebuild_is_immediately_removed(tmp_path: Path) -> None:
    region.create_region(tmp_path, "backend", "FastAPI service internals.", "Summary.")
    search_index.rebuild_index(tmp_path)

    region.delete_region(tmp_path, "backend")

    assert search_index.search(tmp_path, "FastAPI") == []
    assert search_index.index_counts(tmp_path) == {}


def test_create_campaign_after_rebuild_is_immediately_searchable(tmp_path: Path) -> None:
    search_index.rebuild_index(tmp_path)

    campaign.create_campaign(tmp_path, "opening-gambit", "Recover the dragon's hoard.")

    hits = search_index.search(tmp_path, "hoard", object_type="campaign")
    assert len(hits) == 1
    assert hits[0].name == "opening-gambit"
    assert hits[0].status == "draft"


def test_campaign_status_transition_is_immediately_reflected(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    search_index.rebuild_index(tmp_path)

    campaign.open_campaign(tmp_path, "opening-gambit")

    hits = search_index.search(tmp_path, "Body", object_type="campaign")
    assert len(hits) == 1
    assert hits[0].status == "open"


def test_delete_campaign_after_rebuild_is_immediately_removed(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    search_index.rebuild_index(tmp_path)

    campaign.delete_campaign(tmp_path, "opening-gambit")

    assert search_index.search(tmp_path, "Body") == []
    assert search_index.index_counts(tmp_path) == {}


def test_update_world_after_rebuild_is_immediately_reflected(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    search_index.rebuild_index(tmp_path)

    world.update_body(tmp_path, "This world is about a distinctive-world-phrase now.")

    hits = search_index.search(tmp_path, "distinctive-world-phrase", object_type="world")
    assert len(hits) == 1
    assert search_index.index_counts(tmp_path) == {"world": 1}


def test_writes_before_any_rebuild_do_not_create_index_file(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "clean-code", "Keep functions short.", "Summary.")
    region.create_region(tmp_path, "backend", "FastAPI internals.", "Summary.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins.")
    lore.delete_lore(tmp_path, "clean-code")

    assert not search_index_db_path(tmp_path).exists()
    assert search_index.index_counts(tmp_path) is None


def test_delete_campaign_removes_its_own_row_but_leaves_encounters(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins.")
    search_index.rebuild_index(tmp_path)
    assert search_index.index_counts(tmp_path) == {"encounter": 1, "campaign": 1}

    campaign.delete_campaign(tmp_path, "opening-gambit")

    assert search_index.index_counts(tmp_path) == {"encounter": 1}
    assert search_index.search(tmp_path, "goblins")[0].name == "goblin-ambush"


def test_external_file_change_is_invisible_until_rebuild(tmp_path: Path) -> None:
    """Simulates content that changed outside `cac` (e.g. a `git pull`) - it must stay
    invisible to incremental sync until the next explicit `rebuild_index`."""
    search_index.rebuild_index(tmp_path)

    path = lore.lore_path(tmp_path, "manual-lore")
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post("Body mentioning externally-added-phrase.", name="manual-lore", enabled=True)
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")

    assert search_index.search(tmp_path, "externally-added-phrase") == []

    search_index.rebuild_index(tmp_path)

    assert search_index.search(tmp_path, "externally-added-phrase")[0].name == "manual-lore"


def test_sync_write_waits_out_a_concurrent_writer_instead_of_failing(tmp_path: Path) -> None:
    """A second process holding a brief write transaction against sourcebook.db must not make
    an incremental sync from this process fail outright - it should wait (busy timeout) and
    then succeed once the other transaction commits."""
    search_index.rebuild_index(tmp_path)

    blocker = sqlite3.connect(search_index_db_path(tmp_path), check_same_thread=False)
    blocker.execute("BEGIN IMMEDIATE")
    blocker.execute(
        "INSERT INTO sourcebook_fts (object_type, campaign, name, status, updated_on, body) "
        "VALUES ('lore', '', 'placeholder', 'enabled', '', 'placeholder body')"
    )

    def _release_after_delay() -> None:
        time.sleep(0.3)
        blocker.commit()
        blocker.close()

    releaser = threading.Thread(target=_release_after_delay)
    releaser.start()
    try:
        lore.create_lore(tmp_path, "clean-code", "Keep functions short and focused.", "Summary.")
    finally:
        releaser.join()

    hits = search_index.search(tmp_path, "functions", object_type="lore")
    assert len(hits) == 1
    assert hits[0].name == "clean-code"


def test_archive_campaign_leaves_index_rows_untouched_but_excludes_by_default(tmp_path: Path) -> None:
    """Archiving must not call sync_delete on the old path - the campaign's and its encounter's
    index rows survive - but they must now be marked archived and excluded from a default search,
    only reappearing with include_archived=True."""
    _make_campaign(tmp_path)
    campaign.open_campaign(tmp_path, "opening-gambit")
    region.create_region(tmp_path, "default-region", "Body.", "Summary.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "default-region")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Looks good.")
    encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush")
    encounter.complete_encounter(tmp_path, "opening-gambit", "goblin-ambush")
    campaign.complete_campaign(tmp_path, "opening-gambit", "Shipped.")
    search_index.rebuild_index(tmp_path)
    before = search_index.index_counts(tmp_path)

    campaign.archive_campaign(tmp_path, "opening-gambit")

    assert search_index.index_counts(tmp_path) == before
    assert search_index.search(tmp_path, "Body", object_type="campaign") == []
    assert search_index.search(tmp_path, "goblins", object_type="encounter") == []
    campaign_hits = search_index.search(tmp_path, "Body", object_type="campaign", include_archived=True)
    encounter_hits = search_index.search(tmp_path, "goblins", object_type="encounter", include_archived=True)
    assert len(campaign_hits) == 1
    assert campaign_hits[0].archived is True
    assert len(encounter_hits) == 1
    assert encounter_hits[0].archived is True


def test_rebuild_index_includes_archived_campaigns_and_encounters(tmp_path: Path) -> None:
    """A rebuild is disk-driven, not sync_write/sync_delete-driven - it must not silently drop
    archived content just because _reindex_* only used to look at the live directories. Default
    search excludes it; include_archived=True includes it, correctly flagged."""
    _make_campaign(tmp_path)
    campaign.open_campaign(tmp_path, "opening-gambit")
    region.create_region(tmp_path, "default-region", "Body.", "Summary.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "default-region")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Looks good.")
    encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush")
    encounter.complete_encounter(tmp_path, "opening-gambit", "goblin-ambush")
    campaign.complete_campaign(tmp_path, "opening-gambit", "Shipped.")
    campaign.archive_campaign(tmp_path, "opening-gambit")

    count = search_index.rebuild_index(tmp_path)

    assert count == 3
    assert search_index.index_counts(tmp_path) == {"campaign": 1, "encounter": 1, "region": 1}
    assert search_index.search(tmp_path, "Body", object_type="campaign") == []
    assert search_index.search(tmp_path, "goblins", object_type="encounter") == []
    campaign_hits = search_index.search(tmp_path, "Body", object_type="campaign", include_archived=True)
    encounter_hits = search_index.search(tmp_path, "goblins", object_type="encounter", include_archived=True)
    assert len(campaign_hits) == 1
    assert campaign_hits[0].status == "completed"
    assert campaign_hits[0].archived is True
    assert len(encounter_hits) == 1
    assert encounter_hits[0].status == "completed"
    assert encounter_hits[0].archived is True


def test_search_default_excludes_archived_lore_never_flagged(tmp_path: Path) -> None:
    """world/lore/region rows must be archived=0 (not NULL) so the default filter doesn't
    accidentally exclude them too."""
    lore.create_lore(tmp_path, "clean-code", "Keep functions short and focused.", "Summary.")
    search_index.rebuild_index(tmp_path)

    hits = search_index.search(tmp_path, "functions", object_type="lore")

    assert len(hits) == 1
    assert hits[0].archived is False


def test_include_archived_search_reports_mixed_archived_flags(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "campaign-a", "Recover the goblin hoard.")
    campaign.create_campaign(tmp_path, "campaign-b", "Fight the goblin horde.")
    campaign.open_campaign(tmp_path, "campaign-a")
    campaign.complete_campaign(tmp_path, "campaign-a", "Shipped.")
    campaign.archive_campaign(tmp_path, "campaign-a")
    search_index.rebuild_index(tmp_path)

    hits = search_index.search(tmp_path, "goblin", object_type="campaign", include_archived=True)

    assert {hit.name: hit.archived for hit in hits} == {"campaign-a": True, "campaign-b": False}


def test_deleting_an_archived_campaign_removes_its_index_row(tmp_path: Path) -> None:
    """The sync_delete side of the _classify() archive-awareness fix: deleting an already-archived
    campaign (reachable via the read-fallback) must remove its row, not orphan it."""
    _make_campaign(tmp_path)
    campaign.open_campaign(tmp_path, "opening-gambit")
    campaign.complete_campaign(tmp_path, "opening-gambit", "Shipped.")
    campaign.archive_campaign(tmp_path, "opening-gambit")
    search_index.rebuild_index(tmp_path)
    assert search_index.index_counts(tmp_path) == {"campaign": 1}

    campaign.delete_campaign(tmp_path, "opening-gambit")

    assert search_index.index_counts(tmp_path) == {}
    assert search_index.search(tmp_path, "Body", object_type="campaign", include_archived=True) == []
