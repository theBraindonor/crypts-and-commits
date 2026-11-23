from pathlib import Path

import pytest
from cac.core import lore, region, world
from cac.core.references import encoded
from cac.mcp import lore as mcp_lore


def test_lore_get_returns_metadata_summary_and_body(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "clean-code", "Body.", "Summary.")

    result = mcp_lore.lore_get("clean-code")

    assert result["summary"] == "Summary."
    assert result["body"].strip() == "Body."
    assert result["metadata"]["name"] == "clean-code"
    assert "summary" not in result["metadata"]


def test_lore_get_missing_raises() -> None:
    with pytest.raises(lore.LoreNotFoundError):
        mcp_lore.lore_get("missing")


def test_lore_list_returns_items_and_cursor(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "alpha", "Body.", "Summary.")
    lore.create_lore(tmp_path, "beta", "Body.", "Summary.")

    result = mcp_lore.lore_list()

    assert result["items"] == ["alpha", "beta"]
    assert result["next_cursor"] is None


def test_lore_create_returns_new_lore() -> None:
    result = mcp_lore.lore_create("clean-code", "Body.", "Summary.")

    assert result == {"name": "clean-code", "body": "Body."}


def test_lore_update_replaces_body(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "clean-code", "Old.", "Summary.")

    result = mcp_lore.lore_update("clean-code", "New.", "New summary.")

    assert result["body"].strip() == "New."


def test_lore_delete_removes_file(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "clean-code", "Body.", "Summary.")

    result = mcp_lore.lore_delete("clean-code")

    assert not lore.exists(tmp_path, "clean-code")
    assert result["deleted"].endswith("clean-code.md")


def test_lore_set_summary_updates_summary(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "clean-code", "Body.", "Old summary.")

    mcp_lore.lore_set_summary("clean-code", "New summary.")

    assert lore.read_summary(tmp_path, "clean-code") == "New summary."


def test_lore_assign_world_and_unassign_world(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "clean-code", "Body.", "Summary.")

    assigned = mcp_lore.lore_assign_world("clean-code")
    assert assigned["metadata"]["assigned_lore"] == ["clean-code"]

    unassigned = mcp_lore.lore_unassign_world("clean-code")
    assert unassigned["metadata"]["assigned_lore"] == []


def test_lore_assign_region_and_unassign_region(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "clean-code", "Body.", "Summary.")
    region.create_region(tmp_path, "backend", "Body.", "Summary.")

    assigned = mcp_lore.lore_assign_region("clean-code", "backend")
    assert assigned == {"name": "backend", "path": "", "body": "Body."}
    assert region.read_region(tmp_path, "backend").name == "backend"
    assert lore.read_metadata(tmp_path, "clean-code")[0]["assigned_regions"] == ["backend"]

    mcp_lore.lore_unassign_region("clean-code", "backend")
    assert lore.read_metadata(tmp_path, "clean-code")[0]["assigned_regions"] == []


def test_lore_enable_and_disable(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "clean-code", "Body.", "Summary.")

    mcp_lore.lore_disable("clean-code")
    assert lore.read_metadata(tmp_path, "clean-code")[0]["enabled"] is False

    mcp_lore.lore_enable("clean-code")
    assert lore.read_metadata(tmp_path, "clean-code")[0]["enabled"] is True


def test_lore_list_pages_fit_the_response_budget_as_compact_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    names = [f"lore-entry-{index:02d}" for index in range(12)]
    for name in names:
        lore.create_lore(tmp_path, name, "Body.", "Summary.")
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 90)

    seen, cursor, pages = [], None, 0
    while True:
        page = mcp_lore.lore_list(cursor)
        assert len(encoded(page)) <= 90
        seen.extend(page["items"])
        pages += 1
        cursor = page["next_cursor"]
        if cursor is None:
            break

    assert seen == names
    assert pages > 1
