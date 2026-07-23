from pathlib import Path

import pytest

from cac.core import lore


def test_list_lore_returns_empty_when_no_directory(tmp_path: Path) -> None:
    assert lore.list_lore(tmp_path) == []


def test_create_lore_writes_frontmatter_and_body(tmp_path: Path) -> None:
    path = lore.create_lore(tmp_path, "coding-style", "# Coding Style\n\nUse four spaces.")

    assert path == tmp_path / ".sourcebook" / "lore" / "coding-style.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: coding-style" in text
    assert "Use four spaces." in text


def test_create_lore_applies_template_defaults(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "coding-style", "Body.")

    text = (tmp_path / ".sourcebook" / "lore" / "coding-style.md").read_text(encoding="utf-8")

    assert "enabled: true" in text
    assert "assigned_to_world: false" in text
    assert "assigned_regions: []" in text


def test_template_body_returns_placeholder_text() -> None:
    assert "This lore entry has not been described yet." in lore.template_body()


def test_exists_reflects_created_lore(tmp_path: Path) -> None:
    assert lore.exists(tmp_path, "conventions") is False

    lore.create_lore(tmp_path, "conventions", "Body.")

    assert lore.exists(tmp_path, "conventions") is True


def test_exists_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(lore.InvalidLoreNameError):
        lore.exists(tmp_path, "bad name!")


def test_create_lore_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(lore.InvalidLoreNameError):
        lore.create_lore(tmp_path, "bad name!", "body")


def test_create_lore_rejects_duplicate_name(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "duplicate", "first")

    with pytest.raises(lore.LoreAlreadyExistsError):
        lore.create_lore(tmp_path, "duplicate", "second")


def test_list_lore_returns_sorted_names(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "zeta", "z")
    lore.create_lore(tmp_path, "alpha", "a")

    assert lore.list_lore(tmp_path) == ["alpha", "zeta"]


def test_read_lore_returns_name_and_body(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body text.")

    result = lore.read_lore(tmp_path, "conventions")

    assert result.name == "conventions"
    assert result.body.strip() == "Body text."


def test_read_lore_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.read_lore(tmp_path, "missing")


def test_read_metadata_returns_full_frontmatter_and_body(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body text.")
    lore.set_enabled(tmp_path, "conventions", False)
    lore.add_assigned_region(tmp_path, "conventions", "northlands")

    metadata, body = lore.read_metadata(tmp_path, "conventions")

    assert metadata["name"] == "conventions"
    assert metadata["enabled"] is False
    assert metadata["assigned_to_world"] is False
    assert metadata["assigned_regions"] == ["northlands"]
    assert body.strip() == "Body text."


def test_read_metadata_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.read_metadata(tmp_path, "missing")


def test_update_lore_replaces_body(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Original.")

    lore.update_lore(tmp_path, "conventions", "Updated.")

    assert lore.read_lore(tmp_path, "conventions").body.strip() == "Updated."


def test_update_lore_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.update_lore(tmp_path, "missing", "body")


def test_update_lore_preserves_other_frontmatter_attributes(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Original.")
    lore.set_enabled(tmp_path, "conventions", False)
    lore.set_assigned_to_world(tmp_path, "conventions", True)

    lore.update_lore(tmp_path, "conventions", "Updated.")

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "enabled: false" in text
    assert "assigned_to_world: true" in text


def test_set_enabled_toggles_flag(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.")

    lore.set_enabled(tmp_path, "conventions", False)

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "enabled: false" in text


def test_set_enabled_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.set_enabled(tmp_path, "missing", False)


def test_set_assigned_to_world_toggles_flag(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.")

    lore.set_assigned_to_world(tmp_path, "conventions", True)

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "assigned_to_world: true" in text


def test_set_assigned_to_world_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.set_assigned_to_world(tmp_path, "missing", True)


def test_add_assigned_region_appends_region(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.")

    lore.add_assigned_region(tmp_path, "conventions", "northlands")

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "northlands" in text


def test_add_assigned_region_is_idempotent(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.")

    lore.add_assigned_region(tmp_path, "conventions", "northlands")
    result = lore.add_assigned_region(tmp_path, "conventions", "northlands")

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert text.count("northlands") == 1
    assert result.name == "conventions"


def test_add_assigned_region_missing_lore_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.add_assigned_region(tmp_path, "missing", "northlands")


def test_remove_assigned_region_clears_region(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.")
    lore.add_assigned_region(tmp_path, "conventions", "northlands")

    lore.remove_assigned_region(tmp_path, "conventions", "northlands")

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "assigned_regions: []" in text


def test_remove_assigned_region_missing_lore_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.remove_assigned_region(tmp_path, "missing", "northlands")


def test_delete_lore_removes_file(tmp_path: Path) -> None:
    path = lore.create_lore(tmp_path, "conventions", "Body.")

    lore.delete_lore(tmp_path, "conventions")

    assert not path.exists()


def test_delete_lore_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.delete_lore(tmp_path, "missing")
