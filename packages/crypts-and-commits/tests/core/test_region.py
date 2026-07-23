from pathlib import Path

import pytest

from cac.core import lore, region


def test_list_regions_returns_empty_when_no_directory(tmp_path: Path) -> None:
    assert region.list_regions(tmp_path) == []


def test_create_region_writes_frontmatter_and_body(tmp_path: Path) -> None:
    path = region.create_region(tmp_path, "northlands", "# Northlands\n\nCold and mountainous.")

    assert path == tmp_path / ".sourcebook" / "region" / "northlands.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: northlands" in text
    assert "Cold and mountainous." in text


def test_create_region_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(region.InvalidRegionNameError):
        region.create_region(tmp_path, "bad name!", "body")


def test_create_region_allows_periods(tmp_path: Path) -> None:
    path = region.create_region(tmp_path, "v0.1.0-region", "body")

    assert path == tmp_path / ".sourcebook" / "region" / "v0.1.0-region.md"


@pytest.mark.parametrize("name", [".", ".."])
def test_create_region_rejects_reserved_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(region.InvalidRegionNameError):
        region.create_region(tmp_path, name, "body")


def test_create_region_rejects_duplicate_name(tmp_path: Path) -> None:
    region.create_region(tmp_path, "duplicate", "first")

    with pytest.raises(region.RegionAlreadyExistsError):
        region.create_region(tmp_path, "duplicate", "second")


def test_list_regions_returns_sorted_names(tmp_path: Path) -> None:
    region.create_region(tmp_path, "zeta", "z")
    region.create_region(tmp_path, "alpha", "a")

    assert region.list_regions(tmp_path) == ["alpha", "zeta"]


def test_template_body_returns_placeholder_text() -> None:
    assert "This region has not been described yet." in region.template_body()


def test_exists_reflects_created_region(tmp_path: Path) -> None:
    assert region.exists(tmp_path, "northlands") is False

    region.create_region(tmp_path, "northlands", "Body.")

    assert region.exists(tmp_path, "northlands") is True


def test_exists_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(region.InvalidRegionNameError):
        region.exists(tmp_path, "bad name!")


def test_read_region_returns_name_and_body(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body text.")

    result = region.read_region(tmp_path, "northlands")

    assert result.name == "northlands"
    assert result.path == ""
    assert result.body.strip() == "Body text."


def test_read_metadata_returns_full_frontmatter_and_body(tmp_path: Path) -> None:
    region.create_region(tmp_path, "frontend", "Body text.", "src/frontend")

    metadata, body = region.read_metadata(tmp_path, "frontend")

    assert metadata["name"] == "frontend"
    assert metadata["path"] == "src/frontend"
    assert body.strip() == "Body text."


def test_read_metadata_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.read_metadata(tmp_path, "missing")


def test_create_region_accepts_path(tmp_path: Path) -> None:
    path = region.create_region(tmp_path, "frontend", "Body.", "src/frontend")

    text = path.read_text(encoding="utf-8")
    assert "path: src/frontend" in text
    assert region.read_region(tmp_path, "frontend").path == "src/frontend"


def test_set_path_updates_path(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.")

    result = region.set_path(tmp_path, "northlands", "src/backend")

    assert result.path == "src/backend"
    assert region.read_region(tmp_path, "northlands").path == "src/backend"


def test_set_path_missing_region_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.set_path(tmp_path, "missing", "src/backend")


def test_read_region_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.read_region(tmp_path, "missing")


def test_update_region_replaces_body(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Original.")

    region.update_region(tmp_path, "northlands", "Updated.")

    assert region.read_region(tmp_path, "northlands").body.strip() == "Updated."


def test_update_region_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.update_region(tmp_path, "missing", "body")


def test_delete_region_removes_file(tmp_path: Path) -> None:
    path = region.create_region(tmp_path, "northlands", "Body.")

    region.delete_region(tmp_path, "northlands")

    assert not path.exists()


def test_delete_region_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.delete_region(tmp_path, "missing")


def test_assign_lore_updates_region_and_lore(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.")
    lore.create_lore(tmp_path, "conventions", "Body.")

    region.assign_lore(tmp_path, "northlands", "conventions")

    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "conventions" in text
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "northlands" in lore_text
    assert "assigned_regions" in lore_text


def test_assign_lore_is_idempotent(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.")
    lore.create_lore(tmp_path, "conventions", "Body.")

    region.assign_lore(tmp_path, "northlands", "conventions")
    region.assign_lore(tmp_path, "northlands", "conventions")

    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert text.count("conventions") == 1


def test_assign_lore_missing_region_raises(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.")

    with pytest.raises(region.RegionNotFoundError):
        region.assign_lore(tmp_path, "missing", "conventions")


def test_assign_lore_missing_lore_raises(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.")

    with pytest.raises(lore.LoreNotFoundError):
        region.assign_lore(tmp_path, "northlands", "missing")


def test_lore_can_be_assigned_to_multiple_regions(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.")
    region.create_region(tmp_path, "southlands", "Body.")
    lore.create_lore(tmp_path, "conventions", "Body.")

    region.assign_lore(tmp_path, "northlands", "conventions")
    region.assign_lore(tmp_path, "southlands", "conventions")

    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "northlands" in lore_text
    assert "southlands" in lore_text


def test_unassign_lore_updates_region_and_lore(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.")
    lore.create_lore(tmp_path, "conventions", "Body.")
    region.assign_lore(tmp_path, "northlands", "conventions")

    region.unassign_lore(tmp_path, "northlands", "conventions")

    region_text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "conventions" not in region_text
    assert "assigned_regions: []" in lore_text


def test_unassign_lore_missing_region_raises(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.")

    with pytest.raises(region.RegionNotFoundError):
        region.unassign_lore(tmp_path, "missing", "conventions")


def test_unassign_lore_missing_lore_raises(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.")

    with pytest.raises(lore.LoreNotFoundError):
        region.unassign_lore(tmp_path, "northlands", "missing")
