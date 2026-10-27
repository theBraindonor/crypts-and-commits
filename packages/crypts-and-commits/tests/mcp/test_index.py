from pathlib import Path

import pytest
from cac.core import campaign, encounter, search_index
from cac.mcp import index as mcp_index


def test_stale_search_never_returns_hits_and_status_labels_snapshot(tmp_path):
    _make_campaign_with_encounter(tmp_path)
    search_index.rebuild_index(tmp_path)
    path = campaign.campaign_path(tmp_path, "opening-gambit")
    path.write_bytes(path.read_bytes() + b"\nExternal edit")
    result = mcp_index.index_search("goblins")
    assert result["built"] is True and result["stale"] is True
    assert result["hits"] == [] and result["diagnostic"]["code"] == "stale_index"
    assert "developer" in result["diagnostic"]["recovery"]
    assert mcp_index.index_status()["freshness"] == "stale"


def test_boss_filter_and_response_budget(tmp_path, monkeypatch):
    from cac.core import boss, world

    world.initialize_world(tmp_path)
    boss.create_boss(tmp_path, "b001-goal", "uniquebody", "uniquesummary")
    search_index.rebuild_index(tmp_path)
    result = mcp_index.index_search("uniquesummary", object_type="boss")
    assert result["stale"] is False and result["hits"][0]["name"] == "b001-goal"
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 100)
    with pytest.raises(search_index.InvalidSearchQueryError, match="max_results/snippet_tokens"):
        mcp_index.index_search("uniquesummary", object_type="boss")


def _make_campaign_with_encounter(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Fight the goblins in the cave.")


def test_index_status_before_any_rebuild() -> None:
    result = mcp_index.index_status()

    assert result == {"built": False, "counts": {}, "freshness": "missing", "diagnostic": None}


def test_index_status_after_rebuild(tmp_path: Path) -> None:
    _make_campaign_with_encounter(tmp_path)
    search_index.rebuild_index(tmp_path)

    result = mcp_index.index_status()

    assert result == {
        "built": True,
        "counts": {"encounter": 1, "campaign": 1},
        "freshness": "fresh",
        "diagnostic": None,
    }


def test_index_search_before_any_rebuild() -> None:
    result = mcp_index.index_search("goblins")

    assert result == {"built": False, "hits": [], "stale": False}


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


def test_index_search_returns_matching_campaign_hit(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Recover the distinctive-campaign-hoard.")
    search_index.rebuild_index(tmp_path)

    result = mcp_index.index_search("distinctive-campaign-hoard", object_type="campaign")

    assert result["built"] is True
    assert len(result["hits"]) == 1
    hit = result["hits"][0]
    assert hit["object_type"] == "campaign"
    assert hit["campaign"] == ""
    assert hit["name"] == "opening-gambit"
    assert hit["status"] == "draft"


def test_index_search_returns_no_hits_for_no_match(tmp_path: Path) -> None:
    _make_campaign_with_encounter(tmp_path)
    search_index.rebuild_index(tmp_path)

    result = mcp_index.index_search("dragons")

    assert result == {"built": True, "hits": [], "stale": False}


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


def test_index_search_excludes_archived_by_default_and_includes_with_flag(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Recover the goblin hoard.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    campaign.complete_campaign(tmp_path, "opening-gambit", "Shipped.")
    campaign.archive_campaign(tmp_path, "opening-gambit")
    search_index.rebuild_index(tmp_path)

    default_result = mcp_index.index_search("goblin", object_type="campaign")
    included_result = mcp_index.index_search("goblin", object_type="campaign", include_archived=True)

    assert default_result == {"built": True, "hits": [], "stale": False}
    assert included_result["built"] is True
    assert len(included_result["hits"]) == 1
    hit = included_result["hits"][0]
    assert hit["name"] == "opening-gambit"
    assert hit["archived"] is True
