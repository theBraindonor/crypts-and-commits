import sqlite3
from pathlib import Path

import pytest
from cac.core import campaign, encounter, search_index
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

    assert count == 2
    assert search_index.index_counts(tmp_path) == {"encounter": 2}


def test_rebuild_index_is_a_true_drop_and_reindex(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins.")
    search_index.rebuild_index(tmp_path)
    encounter.delete_encounter(tmp_path, "opening-gambit", "goblin-ambush")
    encounter.create_encounter(tmp_path, "opening-gambit", "dragon-hoard", "Recover the hoard.")

    count = search_index.rebuild_index(tmp_path)

    assert count == 1
    assert search_index.index_counts(tmp_path) == {"encounter": 1}


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
        search_index.search(tmp_path, "goblins", object_type="campaign")


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
