from pathlib import Path

import pytest
from cac.core import campaign as campaign_core
from cac.core import encounter as encounter_core
from demo_api.chat.tools import build_tools
from demo_api.chat.tools import campaigns as campaigns_tools
from demo_api.chat.tools import encounters as encounters_tools
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


def test_build_tools_aggregates_every_domain(tmp_path: Path) -> None:
    tools = build_tools(tmp_path)

    names = {t.name for t in tools}
    assert names == {"list_campaigns", "get_campaign", "list_encounters", "get_encounter"}
