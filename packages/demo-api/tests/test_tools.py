from pathlib import Path

import pytest
from cac.core import campaign as campaign_core
from cac.core import encounter as encounter_core
from cac.core import lore as lore_core
from cac.core import region as region_core
from cac.core import search_index as search_index_core
from cac.core import world as world_core
from demo_api.chat.tools import build_tools
from demo_api.chat.tools import campaigns as campaigns_tools
from demo_api.chat.tools import encounters as encounters_tools
from demo_api.chat.tools import lore as lore_tools
from demo_api.chat.tools import region as region_tools
from demo_api.chat.tools import search as search_tools
from demo_api.chat.tools import world as world_tools
from langchain_core.tools import BaseTool


def _make_campaign(root: Path, name: str, *, open_it: bool = True) -> None:
    campaign_core.create_campaign(root, name, "Campaign body.")
    if open_it:
        campaign_core.open_campaign(root, name)


def _tool_by_name(tools: list[BaseTool], name: str) -> BaseTool:
    return next(t for t in tools if t.name == name)


def test_list_campaigns_returns_name_and_status(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "opening-gambit")
    tools = campaigns_tools.build_tools(tmp_path)

    result = _tool_by_name(tools, "list_campaigns").invoke({})

    assert result == [{"name": "opening-gambit", "status": "open"}]


def test_get_campaign_returns_status_and_body(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "opening-gambit")
    tools = campaigns_tools.build_tools(tmp_path)

    result = _tool_by_name(tools, "get_campaign").invoke({"name": "opening-gambit"})

    assert result == {"name": "opening-gambit", "status": "open", "body": "Campaign body."}


def test_get_campaign_missing_raises(tmp_path: Path) -> None:
    tools = campaigns_tools.build_tools(tmp_path)

    with pytest.raises(campaign_core.CampaignNotFoundError):
        _tool_by_name(tools, "get_campaign").invoke({"name": "missing"})


def test_list_encounters_defaults_to_active_campaign(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "opening-gambit")
    encounter_core.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    tools = encounters_tools.build_tools(tmp_path)

    result = _tool_by_name(tools, "list_encounters").invoke({})

    assert result == ["goblin-ambush"]


def test_list_encounters_no_active_campaign_raises(tmp_path: Path) -> None:
    tools = encounters_tools.build_tools(tmp_path)

    with pytest.raises(campaign_core.NoActiveCampaignError):
        _tool_by_name(tools, "list_encounters").invoke({})


def test_get_encounter_returns_status_regions_and_body(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "opening-gambit")
    encounter_core.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "## Requirements\n\nStop them.")
    tools = encounters_tools.build_tools(tmp_path)

    result = _tool_by_name(tools, "get_encounter").invoke({"name": "goblin-ambush"})

    assert result == {
        "name": "goblin-ambush",
        "campaign": "opening-gambit",
        "status": "draft",
        "regions": [],
        "depends_on": [],
        "body": "## Requirements\n\nStop them.",
    }


def test_get_encounter_missing_raises(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "opening-gambit")
    tools = encounters_tools.build_tools(tmp_path)

    with pytest.raises(encounter_core.EncounterNotFoundError):
        _tool_by_name(tools, "get_encounter").invoke({"name": "missing"})


def test_get_encounter_explicit_campaign_overrides_active(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "opening-gambit")
    _make_campaign(tmp_path, "second-front", open_it=False)
    encounter_core.create_encounter(tmp_path, "second-front", "flank-attack", "Body.")
    tools = encounters_tools.build_tools(tmp_path)

    result = _tool_by_name(tools, "get_encounter").invoke({"name": "flank-attack", "campaign": "second-front"})

    assert result["campaign"] == "second-front"


def test_get_world_returns_name_lore_and_body(tmp_path: Path) -> None:
    world_core.initialize_world(tmp_path)
    tools = world_tools.build_tools(tmp_path)

    result = _tool_by_name(tools, "get_world").invoke({})

    assert result == {
        "name": "unnamed_world",
        "assigned_lore": [],
        "body": "# Unnamed World\n\nBe sure to edit this world definition file before starting development!",
    }


def test_list_and_get_region_returns_path_and_assigned_lore(tmp_path: Path) -> None:
    lore_core.create_lore(tmp_path, "no-secrets", "Body.", "Summary.")
    region_core.create_region(tmp_path, "backend", "Region body.", "Summary.", "packages/backend")
    region_core.assign_lore(tmp_path, "backend", "no-secrets")
    tools = region_tools.build_tools(tmp_path)

    listed = _tool_by_name(tools, "list_regions").invoke({})
    fetched = _tool_by_name(tools, "get_region").invoke({"name": "backend"})

    assert listed == ["backend"]
    assert fetched == {
        "name": "backend",
        "path": "packages/backend",
        "assigned_lore": ["no-secrets"],
        "body": "Region body.",
    }


def test_get_region_missing_raises(tmp_path: Path) -> None:
    tools = region_tools.build_tools(tmp_path)

    with pytest.raises(region_core.RegionNotFoundError):
        _tool_by_name(tools, "get_region").invoke({"name": "missing"})


def test_list_and_get_lore_returns_flags_and_body(tmp_path: Path) -> None:
    region_core.create_region(tmp_path, "backend", "Region body.", "Summary.")
    lore_core.create_lore(tmp_path, "no-secrets", "Lore body.", "Summary.")
    lore_core.set_enabled(tmp_path, "no-secrets", False)
    lore_core.set_assigned_to_world(tmp_path, "no-secrets", True)
    lore_core.add_assigned_region(tmp_path, "no-secrets", "backend")
    tools = lore_tools.build_tools(tmp_path)

    listed = _tool_by_name(tools, "list_lore").invoke({})
    fetched = _tool_by_name(tools, "get_lore").invoke({"name": "no-secrets"})

    assert listed == ["no-secrets"]
    assert fetched == {
        "name": "no-secrets",
        "enabled": False,
        "assigned_to_world": True,
        "assigned_regions": ["backend"],
        "body": "Lore body.",
    }


def test_get_lore_missing_raises(tmp_path: Path) -> None:
    tools = lore_tools.build_tools(tmp_path)

    with pytest.raises(lore_core.LoreNotFoundError):
        _tool_by_name(tools, "get_lore").invoke({"name": "missing"})


def test_search_sourcebook_unavailable_when_index_not_built(tmp_path: Path) -> None:
    tools = search_tools.build_tools(tmp_path)

    result = _tool_by_name(tools, "search_sourcebook").invoke({"phrase": "anything"})

    assert result == {"available": False, "hits": []}


def test_search_sourcebook_finds_indexed_lore_and_filters_by_object_type(tmp_path: Path) -> None:
    lore_core.create_lore(tmp_path, "no-secrets", "Never commit API keys.", "Summary.")
    search_index_core.rebuild_index(tmp_path)
    tools = search_tools.build_tools(tmp_path)
    search_tool = _tool_by_name(tools, "search_sourcebook")

    matched = search_tool.invoke({"phrase": "API keys"})
    filtered_out = search_tool.invoke({"phrase": "API keys", "object_type": "region"})

    assert matched["available"] is True
    assert any(hit["object_type"] == "lore" and hit["name"] == "no-secrets" for hit in matched["hits"])
    assert filtered_out == {"available": True, "hits": []}


def test_search_sourcebook_empty_phrase_raises(tmp_path: Path) -> None:
    search_index_core.rebuild_index(tmp_path)
    tools = search_tools.build_tools(tmp_path)

    with pytest.raises(search_index_core.EmptySearchPhraseError):
        _tool_by_name(tools, "search_sourcebook").invoke({"phrase": ""})


def test_build_tools_aggregates_every_domain(tmp_path: Path) -> None:
    tools = build_tools(tmp_path)

    names = {t.name for t in tools}
    assert names == {
        "list_campaigns",
        "get_campaign",
        "list_encounters",
        "get_encounter",
        "get_world",
        "list_regions",
        "get_region",
        "list_lore",
        "get_lore",
        "search_sourcebook",
    }
