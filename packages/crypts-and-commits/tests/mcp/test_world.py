from pathlib import Path

import frontmatter
import pytest
from cac.core import world
from cac.mcp import world as mcp_world


def test_world_get_exposes_legacy_branch_defaults_without_writes(legacy_world: Path) -> None:
    before = legacy_world.read_bytes()
    modified = legacy_world.stat().st_mtime_ns

    result = mcp_world.world_get()

    assert set(result) == {"metadata", "body"}
    assert result["metadata"]["merge_target_branch"] == "main"
    assert result["metadata"]["planning_branch"] == "planning"
    assert legacy_world.read_bytes() == before
    assert legacy_world.stat().st_mtime_ns == modified


@pytest.mark.parametrize("key", ["merge_target_branch", "planning_branch"])
def test_world_set_exposes_overrides_and_defaults_without_backfill(legacy_world: Path, key: str) -> None:
    result = mcp_world.world_set(key, "team/custom")

    assert result == mcp_world.world_get()
    assert result["metadata"][key] == "team/custom"
    other = "planning_branch" if key == "merge_target_branch" else "merge_target_branch"
    assert other in result["metadata"]
    assert other not in frontmatter.load(legacy_world)


def test_world_body_update_returns_defaults_without_backfill(legacy_world: Path) -> None:
    result = mcp_world.world_set_body("Edited world.")

    assert result["metadata"]["merge_target_branch"] == "main"
    assert result["metadata"]["planning_branch"] == "planning"
    assert result == mcp_world.world_get()
    persisted = frontmatter.load(legacy_world)
    assert "merge_target_branch" not in persisted
    assert "planning_branch" not in persisted


def test_world_get_returns_metadata_and_body(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    world.update_body(tmp_path, "The world body.")

    result = mcp_world.world_get()

    assert result["body"].strip() == "The world body."
    assert result["metadata"]["name"]


def test_world_get_missing_world_raises() -> None:
    with pytest.raises(world.WorldNotFoundError):
        mcp_world.world_get()


def test_world_set_updates_attribute(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = mcp_world.world_set("name", "New Name")

    assert result["metadata"]["name"] == "New Name"


def test_world_set_body_replaces_body(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = mcp_world.world_set_body("Replaced body.")

    assert result["body"].strip() == "Replaced body."


def test_world_get_from_a_subdirectory_finds_the_root_sourcebook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    world.initialize_world(tmp_path)
    world.update_body(tmp_path, "The world body.")
    nested = tmp_path / "packages" / "crypts-and-commits"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    result = mcp_world.world_get()

    assert result["body"].strip() == "The world body."
    assert not (nested / ".sourcebook").exists()
