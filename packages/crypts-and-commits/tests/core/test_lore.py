from pathlib import Path

import pytest

from cac.core import frontmatter_utils, lore


def test_list_lore_returns_empty_when_no_directory(tmp_path: Path) -> None:
    assert lore.list_lore(tmp_path) == []


def test_create_lore_writes_frontmatter_and_body(tmp_path: Path) -> None:
    path = lore.create_lore(tmp_path, "coding-style", "# Coding Style\n\nUse four spaces.", "Summary.")

    assert path == tmp_path / ".sourcebook" / "lore" / "coding-style.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: coding-style" in text
    assert "Use four spaces." in text


def test_create_lore_applies_template_defaults(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "coding-style", "Body.", "Summary.")

    text = (tmp_path / ".sourcebook" / "lore" / "coding-style.md").read_text(encoding="utf-8")

    assert "enabled: true" in text
    assert "assigned_to_world: false" in text
    assert "assigned_regions: []" in text


def test_template_body_returns_placeholder_text() -> None:
    assert "This lore entry has not been described yet." in lore.template_body()


def test_exists_reflects_created_lore(tmp_path: Path) -> None:
    assert lore.exists(tmp_path, "conventions") is False

    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    assert lore.exists(tmp_path, "conventions") is True


def test_exists_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(lore.InvalidLoreNameError):
        lore.exists(tmp_path, "bad name!")


def test_create_lore_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(lore.InvalidLoreNameError):
        lore.create_lore(tmp_path, "bad name!", "body", "Summary.")


def test_create_lore_allows_periods(tmp_path: Path) -> None:
    path = lore.create_lore(tmp_path, "v0.1.0-style", "body", "Summary.")

    assert path == tmp_path / ".sourcebook" / "lore" / "v0.1.0-style.md"


@pytest.mark.parametrize("name", [".", ".."])
def test_create_lore_rejects_reserved_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(lore.InvalidLoreNameError):
        lore.create_lore(tmp_path, name, "body", "Summary.")


def test_create_lore_rejects_duplicate_name(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "duplicate", "first", "Summary.")

    with pytest.raises(lore.LoreAlreadyExistsError):
        lore.create_lore(tmp_path, "duplicate", "second", "Summary.")


def test_list_lore_returns_sorted_names(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "zeta", "z", "Summary.")
    lore.create_lore(tmp_path, "alpha", "a", "Summary.")

    assert lore.list_lore(tmp_path) == ["alpha", "zeta"]


def test_read_lore_returns_name_and_body(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body text.", "Summary.")

    result = lore.read_lore(tmp_path, "conventions")

    assert result.name == "conventions"
    assert result.body.strip() == "Body text."


def test_read_lore_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.read_lore(tmp_path, "missing")


def test_read_metadata_returns_full_frontmatter_and_body(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body text.", "Summary.")
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


def test_create_lore_stores_summary(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "A routing signal.")

    assert lore.read_summary(tmp_path, "conventions") == "A routing signal."


def test_create_lore_rejects_over_cap_summary_without_writing(tmp_path: Path) -> None:
    with pytest.raises(lore.SummaryTooLongError):
        lore.create_lore(tmp_path, "conventions", "Body.", "x" * 501)

    assert not lore.exists(tmp_path, "conventions")


def test_update_lore_replaces_body(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Original.", "Summary.")

    lore.update_lore(tmp_path, "conventions", "Updated.", "Summary.")

    assert lore.read_lore(tmp_path, "conventions").body.strip() == "Updated."


def test_update_lore_regenerates_summary(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Original.", "Original summary.")

    lore.update_lore(tmp_path, "conventions", "Updated.", "Updated summary.")

    assert lore.read_lore(tmp_path, "conventions").body.strip() == "Updated."
    assert lore.read_summary(tmp_path, "conventions") == "Updated summary."


def test_update_lore_rejects_over_cap_summary_without_writing(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Original.", "Original summary.")

    with pytest.raises(lore.SummaryTooLongError):
        lore.update_lore(tmp_path, "conventions", "Updated.", "x" * 501)

    # Never-stale: the rejected write left the original body and summary intact.
    assert lore.read_lore(tmp_path, "conventions").body.strip() == "Original."
    assert lore.read_summary(tmp_path, "conventions") == "Original summary."


def test_update_lore_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.update_lore(tmp_path, "missing", "body", "Summary.")


def test_update_lore_preserves_other_frontmatter_attributes(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Original.", "Summary.")
    lore.set_enabled(tmp_path, "conventions", False)
    lore.set_assigned_to_world(tmp_path, "conventions", True)

    lore.update_lore(tmp_path, "conventions", "Updated.", "Summary.")

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "enabled: false" in text
    assert "assigned_to_world: true" in text


def test_set_summary_round_trips(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    lore.set_summary(tmp_path, "conventions", "A brief routing signal.")

    assert lore.read_summary(tmp_path, "conventions") == "A brief routing signal."


def test_set_summary_accepts_value_at_cap(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    lore.set_summary(tmp_path, "conventions", "x" * 500)

    assert lore.read_summary(tmp_path, "conventions") == "x" * 500


def test_set_summary_rejects_value_over_cap(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    with pytest.raises(lore.SummaryTooLongError):
        lore.set_summary(tmp_path, "conventions", "x" * 501)


def test_set_summary_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.set_summary(tmp_path, "missing", "text")


def test_read_summary_returns_placeholder_when_absent(tmp_path: Path) -> None:
    # A body written directly without the write-path setter has no summary; the
    # read path must still return the explicit placeholder.
    lore_dir = tmp_path / ".sourcebook" / "lore"
    lore_dir.mkdir(parents=True)
    (lore_dir / "conventions.md").write_text("---\nname: conventions\n---\n\nBody.\n", encoding="utf-8")

    assert lore.read_summary(tmp_path, "conventions") == frontmatter_utils.SUMMARY_ABSENT_MESSAGE


def test_read_summary_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.read_summary(tmp_path, "missing")


def test_set_summary_preserves_other_frontmatter_attributes(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")
    lore.set_assigned_to_world(tmp_path, "conventions", True)

    lore.set_summary(tmp_path, "conventions", "A brief routing signal.")

    metadata, body = lore.read_metadata(tmp_path, "conventions")
    assert metadata["assigned_to_world"] is True
    assert body.strip() == "Body."


def test_set_enabled_toggles_flag(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    lore.set_enabled(tmp_path, "conventions", False)

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "enabled: false" in text


def test_set_enabled_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.set_enabled(tmp_path, "missing", False)


def test_set_assigned_to_world_toggles_flag(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    lore.set_assigned_to_world(tmp_path, "conventions", True)

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "assigned_to_world: true" in text


def test_set_assigned_to_world_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.set_assigned_to_world(tmp_path, "missing", True)


def test_add_assigned_region_appends_region(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    lore.add_assigned_region(tmp_path, "conventions", "northlands")

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "northlands" in text


def test_add_assigned_region_is_idempotent(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    lore.add_assigned_region(tmp_path, "conventions", "northlands")
    result = lore.add_assigned_region(tmp_path, "conventions", "northlands")

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert text.count("northlands") == 1
    assert result.name == "conventions"


def test_add_assigned_region_missing_lore_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.add_assigned_region(tmp_path, "missing", "northlands")


def test_remove_assigned_region_clears_region(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")
    lore.add_assigned_region(tmp_path, "conventions", "northlands")

    lore.remove_assigned_region(tmp_path, "conventions", "northlands")

    text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "assigned_regions: []" in text


def test_remove_assigned_region_missing_lore_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.remove_assigned_region(tmp_path, "missing", "northlands")


def test_delete_lore_removes_file(tmp_path: Path) -> None:
    path = lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    lore.delete_lore(tmp_path, "conventions")

    assert not path.exists()


def test_delete_lore_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(lore.LoreNotFoundError):
        lore.delete_lore(tmp_path, "missing")
