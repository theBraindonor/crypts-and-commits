import asyncio

import pytest
from cac.core import boss, config, references, world
from cac.core import rumor as rumor_core
from cac.mcp import rumor as api
from cac.mcp.instance import mcp

TOOLS = {
    "rumor_list",
    "rumor_get",
    "rumor_create",
    "rumor_update",
    "rumor_promote",
    "rumor_dismiss",
    "rumor_reopen",
    "rumor_archive",
    "rumor_renumber",
}


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)


def test_exactly_nine_rumor_tools_are_registered():
    names = {tool.name for tool in asyncio.run(mcp.list_tools())}
    assert {name for name in names if name.startswith("rumor")} == TOOLS


def test_create_and_update_require_body_summary_and_origin():
    with pytest.raises(TypeError):
        api.rumor_create("r001-idea", "Body", "Summary")
    with pytest.raises(TypeError):
        api.rumor_update("r001-idea", "Body", "Summary")
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    for name in ("rumor_create", "rumor_update"):
        assert set(tools[name].input_schema["required"]) == {"name", "body", "summary", "origin"}
    assert set(tools["rumor_dismiss"].input_schema["required"]) == {"name", "message"}
    assert set(tools["rumor_reopen"].input_schema["required"]) == {"name", "message"}
    assert set(tools["rumor_promote"].input_schema["required"]) == {"name", "boss"}


def test_lifecycle_through_short_references(tmp_path):
    created = api.rumor_create("r001-idea", "[notes]", "Summary", "Standup")
    assert created["identity"] == {"canonical": "r001-idea", "short": "r001", "reason": None}
    assert created["metadata"]["origin"] == "Standup"
    assert api.rumor_update("r001", "New", "New summary", "Retro")["body"] == "New"
    boss.create_boss(tmp_path, "b001-goal", "Goal", "Summary")
    promoted = api.rumor_promote("r001", "b001")
    assert promoted["metadata"]["status"] == "promoted" and promoted["metadata"]["boss"] == "b001-goal"
    assert api.rumor_reopen("r001", "Not yet")["metadata"]["status"] == "open"
    renumbered = api.rumor_renumber("r001", "r002-idea")
    assert renumbered["identity"] == {"canonical": "r002-idea", "short": "r002", "reason": None}
    assert api.rumor_dismiss("r002", "Out of scope")["metadata"]["resolution"] == "Out of scope"
    archived = api.rumor_archive("r002")
    assert archived["metadata"]["archived"] is True
    assert api.rumor_get("r002")["metadata"]["history"][-1]["action"] == "dismiss"


def test_list_pages_identities_and_filters_status(monkeypatch):
    for number in range(1, 31):
        api.rumor_create(f"r{number:03d}-idea", "", "Summary", "Origin")
    api.rumor_dismiss("r002", "No")
    assert api.rumor_list(status="dismissed")["items"] == ["r002-idea"]
    with pytest.raises(ValueError, match="Unknown rumor status"):
        api.rumor_list(status="closed")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 900)
    names, cursor = [], None
    while True:
        page = api.rumor_list(cursor)
        assert len(references.encoded(page)) <= 900
        assert len(page["items"]) == len(page["identities"])
        names.extend(page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert names == [f"r{number:03d}-idea" for number in range(1, 31)]


def test_get_continues_long_bodies(tmp_path, monkeypatch):
    text = "[tool.ruff] 🐉\r\n" * 200
    api.rumor_create("r001-idea", text, "Summary", "Origin")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 900)
    parts, cursor = [], None
    while True:
        page = api.rumor_get("r001", cursor)
        assert len(references.encoded(page)) <= 900
        parts.append(page["body"])
        # A complete final page keeps the plain get shape, without a next_cursor key.
        cursor = page.get("next_cursor")
        if cursor is None:
            break
    assert len(parts) > 1
    # Rumors are frontmatter records like bosses, so the stored body is the normalized one.
    assert "".join(parts) == rumor_core.read_metadata(tmp_path, "r001-idea")[1]
    assert "[tool.ruff] 🐉" in parts[0]


def test_invalid_inputs_raise_without_writes(tmp_path):
    with pytest.raises(ValueError):
        api.rumor_create("r001-idea", "Body", "Summary", " ")
    with pytest.raises(FileNotFoundError):
        api.rumor_get("r404")
    api.rumor_create("r001-idea", "Body", "Summary", "Origin")
    with pytest.raises(FileNotFoundError):
        api.rumor_promote("r001", "b404")
    assert api.rumor_get("r001")["metadata"]["status"] == "open"
