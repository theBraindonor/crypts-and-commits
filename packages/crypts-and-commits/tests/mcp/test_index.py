from pathlib import Path

import pytest
from cac.core import campaign, encounter, search_index
from cac.mcp import index as mcp_index


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def _make_campaign_with_encounter(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins in the cave.")


def test_index_status_before_any_rebuild() -> None:
    result = mcp_index.index_status()

    assert result == {"built": False, "counts": {}}


def test_index_status_after_rebuild(tmp_path: Path) -> None:
    _make_campaign_with_encounter(tmp_path)
    search_index.rebuild_index(tmp_path)

    result = mcp_index.index_status()

    assert result == {"built": True, "counts": {"encounter": 1}}


def test_index_search_before_any_rebuild() -> None:
    result = mcp_index.index_search("goblins")

    assert result == {"built": False, "hits": []}


def test_index_search_returns_matching_hits(tmp_path: Path) -> None:
    _make_campaign_with_encounter(tmp_path)
    search_index.rebuild_index(tmp_path)

    result = mcp_index.index_search("goblins")

    assert result["built"] is True
    assert len(result["hits"]) == 1
    hit = result["hits"][0]
    assert hit["object_type"] == "encounter"
    assert hit["campaign"] == "opening-gambit"
    assert hit["name"] == "goblin-ambush"
    assert "goblins" in hit["excerpt"].lower()


def test_index_search_returns_no_hits_for_no_match(tmp_path: Path) -> None:
    _make_campaign_with_encounter(tmp_path)
    search_index.rebuild_index(tmp_path)

    result = mcp_index.index_search("dragons")

    assert result == {"built": True, "hits": []}


def test_index_search_empty_phrase_raises(tmp_path: Path) -> None:
    _make_campaign_with_encounter(tmp_path)
    search_index.rebuild_index(tmp_path)

    with pytest.raises(search_index.EmptySearchPhraseError):
        mcp_index.index_search("   ")


def test_index_search_invalid_object_type_raises(tmp_path: Path) -> None:
    _make_campaign_with_encounter(tmp_path)
    search_index.rebuild_index(tmp_path)

    with pytest.raises(search_index.InvalidSearchQueryError):
        mcp_index.index_search("goblins", object_type="not-a-type")


def test_index_search_invalid_snippet_tokens_raises(tmp_path: Path) -> None:
    _make_campaign_with_encounter(tmp_path)
    search_index.rebuild_index(tmp_path)

    with pytest.raises(search_index.InvalidSearchQueryError):
        mcp_index.index_search("goblins", snippet_tokens=0)
