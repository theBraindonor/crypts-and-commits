from pathlib import Path

import pytest
from cac.core import region
from cac.mcp import region as mcp_region


def test_region_get_returns_metadata_summary_and_body(tmp_path: Path) -> None:
    region.create_region(tmp_path, "backend", "Body.", "Summary.", "src/backend")

    result = mcp_region.region_get("backend")

    assert result["summary"] == "Summary."
    assert result["body"].strip() == "Body."
    assert result["metadata"]["path"] == "src/backend"
    assert "summary" not in result["metadata"]


def test_region_get_missing_raises() -> None:
    with pytest.raises(region.RegionNotFoundError):
        mcp_region.region_get("missing")


def test_region_list_returns_items_and_cursor(tmp_path: Path) -> None:
    region.create_region(tmp_path, "backend", "Body.", "Summary.")
    region.create_region(tmp_path, "frontend", "Body.", "Summary.")

    result = mcp_region.region_list()

    assert result["items"] == ["backend", "frontend"]
    assert result["next_cursor"] is None


def test_region_create_returns_new_region() -> None:
    result = mcp_region.region_create("backend", "Body.", "Summary.", "src/backend")

    assert result == {"name": "backend", "path": "src/backend", "body": "Body."}


def test_region_update_replaces_body(tmp_path: Path) -> None:
    region.create_region(tmp_path, "backend", "Old.", "Summary.")

    result = mcp_region.region_update("backend", "New.", "New summary.")

    assert result["body"].strip() == "New."


def test_region_delete_removes_file(tmp_path: Path) -> None:
    region.create_region(tmp_path, "backend", "Body.", "Summary.")

    result = mcp_region.region_delete("backend")

    assert not region.exists(tmp_path, "backend")
    assert result["deleted"].endswith("backend.md")


def test_region_set_summary_updates_summary(tmp_path: Path) -> None:
    region.create_region(tmp_path, "backend", "Body.", "Old summary.")

    mcp_region.region_set_summary("backend", "New summary.")

    assert region.read_summary(tmp_path, "backend") == "New summary."


def test_region_set_path_updates_path(tmp_path: Path) -> None:
    region.create_region(tmp_path, "backend", "Body.", "Summary.")

    result = mcp_region.region_set_path("backend", "packages/backend")

    assert result["path"] == "packages/backend"
    assert region.read_region(tmp_path, "backend").path == "packages/backend"
