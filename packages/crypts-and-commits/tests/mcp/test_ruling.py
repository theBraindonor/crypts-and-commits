import asyncio

import pytest
from cac.core import campaign, config, encounter, references, world
from cac.core import ruling as ruling_core
from cac.mcp import ruling as api
from cac.mcp.instance import mcp

TOOLS = {
    "ruling_list",
    "ruling_get",
    "ruling_create",
    "ruling_update",
    "ruling_canonize",
    "ruling_note",
    "ruling_reopen",
    "ruling_archive",
}
NAME = "c002-e001-slugs-unique"
IDENTITY = {"canonical": NAME, "short": None, "reason": "canonical_only"}


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c002-rulings", "Tactics")
    encounter.create_encounter(tmp_path, "c002-rulings", "e001-core", "Plan")
    campaign.open_campaign(tmp_path, "c002-rulings")


def test_exactly_eight_ruling_tools_are_registered():
    names = {tool.name for tool in asyncio.run(mcp.list_tools())}
    assert {name for name in names if name.startswith("ruling")} == TOOLS


def test_required_arguments_and_body_has_no_editor_fallback():
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    for name in ("ruling_create", "ruling_update"):
        assert set(tools[name].input_schema["required"]) == {"name", "body", "summary", "origin"}
    for name in ("ruling_canonize", "ruling_note", "ruling_reopen"):
        assert set(tools[name].input_schema["required"]) == {"name", "message"}
    assert "canonical names only" in tools["ruling_get"].description


def test_lifecycle_with_canonical_identity():
    created = api.ruling_create(NAME, "[decision]", "Summary", "GM")
    assert created["identity"] == IDENTITY
    assert created["metadata"]["campaign"] == "c002-rulings" and created["metadata"]["encounter"] == "e001-core"
    assert api.ruling_update(NAME, "New", "New summary", "Review")["body"] == "New"
    assert api.ruling_canonize(NAME, "Added lore")["metadata"]["resolution"] == "Added lore"
    reopened = api.ruling_reopen(NAME, "Revisit")
    assert reopened["metadata"]["status"] == "recorded" and reopened["metadata"]["resolution"] is None
    assert api.ruling_note(NAME, "Local only")["metadata"]["status"] == "noted"
    archived = api.ruling_archive(NAME)
    assert archived["metadata"]["archived"] is True and archived["identity"] == IDENTITY
    assert [entry["action"] for entry in api.ruling_get(NAME)["metadata"]["history"]] == [
        "canonize",
        "reopen",
        "note",
    ]


def test_list_pages_identities_and_filters_status(monkeypatch):
    for number in range(1, 31):
        api.ruling_create(f"c002-e000-ruling{number:02d}", "", "Summary", "GM")
    api.ruling_note("c002-e000-ruling02", "Local")
    assert api.ruling_list(status="noted")["items"] == ["c002-e000-ruling02"]
    with pytest.raises(ValueError, match="Unknown ruling status"):
        api.ruling_list(status="open")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 900)
    names, cursor = [], None
    while True:
        page = api.ruling_list(cursor)
        assert len(references.encoded(page)) <= 900
        assert len(page["items"]) == len(page["identities"])
        names.extend(page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert names == [f"c002-e000-ruling{number:02d}" for number in range(1, 31)]


def test_get_continues_long_bodies(tmp_path, monkeypatch):
    text = "[tool.ruff] 🐉\r\n" * 200
    api.ruling_create(NAME, text, "Summary", "GM")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 900)
    parts, cursor = [], None
    while True:
        page = api.ruling_get(NAME, cursor)
        assert len(references.encoded(page)) <= 900
        parts.append(page["body"])
        cursor = page.get("next_cursor")
        if cursor is None:
            break
    assert len(parts) > 1
    assert "".join(parts) == ruling_core.read_metadata(tmp_path, NAME)[1]


def test_invalid_inputs_raise_without_writes(tmp_path):
    with pytest.raises(ValueError):
        api.ruling_create(NAME, "Body", "Summary", " ")
    with pytest.raises(FileNotFoundError):
        api.ruling_get("c002-e001-missing")
    with pytest.raises(FileNotFoundError):
        api.ruling_create("c002-e009-missing", "Body", "Summary", "GM")
    campaign.pause_campaign(tmp_path, "c002-rulings")
    with pytest.raises(ValueError, match="rumor"):
        api.ruling_create(NAME, "Body", "Summary", "GM")
    assert not ruling_core.ruling_dir(tmp_path).exists()


def test_ruling_list_description_names_every_status() -> None:
    import re

    description = api.ruling_list.__doc__ or ""
    missing = [s for s in config.RULING_STATUSES if not re.search(rf"\b{re.escape(s)}\b", description)]
    assert missing == [], f"ruling_list description omits statuses: {missing}"
