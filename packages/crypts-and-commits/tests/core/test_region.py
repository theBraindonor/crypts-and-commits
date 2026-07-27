from datetime import UTC, datetime
from pathlib import Path

import pytest
from cac.core import frontmatter_utils, git_utils, lore, region

_FIXED_TIME = datetime(2026, 7, 23, 18, 4, 12, tzinfo=UTC)


def _set_identity(monkeypatch: pytest.MonkeyPatch, *, user: str = "John Hoff", when: datetime = _FIXED_TIME) -> None:
    monkeypatch.setattr(git_utils, "current_git_user", lambda root: user)
    monkeypatch.setattr(frontmatter_utils, "utcnow", lambda: when)


@pytest.fixture(autouse=True)
def _default_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_identity(monkeypatch)


def test_list_regions_returns_empty_when_no_directory(tmp_path: Path) -> None:
    assert region.list_regions(tmp_path) == []


def test_create_region_writes_frontmatter_and_body(tmp_path: Path) -> None:
    path = region.create_region(tmp_path, "northlands", "# Northlands\n\nCold and mountainous.", "Summary.")

    assert path == tmp_path / ".sourcebook" / "region" / "northlands.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: northlands" in text
    assert "Cold and mountainous." in text


def test_create_region_sets_created_and_updated_fields(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    metadata, _ = region.read_metadata(tmp_path, "northlands")

    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "John Hoff"
    assert metadata["updated_on"] == "2026-07-23T18:04:12Z"


def test_create_region_propagates_git_identity_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    assert not region.exists(tmp_path, "northlands")


def test_create_region_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(region.InvalidRegionNameError):
        region.create_region(tmp_path, "bad name!", "body", "Summary.")


def test_create_region_allows_periods(tmp_path: Path) -> None:
    path = region.create_region(tmp_path, "v0.1.0-region", "body", "Summary.")

    assert path == tmp_path / ".sourcebook" / "region" / "v0.1.0-region.md"


@pytest.mark.parametrize("name", [".", ".."])
def test_create_region_rejects_reserved_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(region.InvalidRegionNameError):
        region.create_region(tmp_path, name, "body", "Summary.")


def test_create_region_rejects_duplicate_name(tmp_path: Path) -> None:
    region.create_region(tmp_path, "duplicate", "first", "Summary.")

    with pytest.raises(region.RegionAlreadyExistsError):
        region.create_region(tmp_path, "duplicate", "second", "Summary.")


def test_list_regions_returns_sorted_names(tmp_path: Path) -> None:
    region.create_region(tmp_path, "zeta", "z", "Summary.")
    region.create_region(tmp_path, "alpha", "a", "Summary.")

    assert region.list_regions(tmp_path) == ["alpha", "zeta"]


def test_template_body_returns_placeholder_text() -> None:
    assert "This region has not been described yet." in region.template_body()


def test_exists_reflects_created_region(tmp_path: Path) -> None:
    assert region.exists(tmp_path, "northlands") is False

    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    assert region.exists(tmp_path, "northlands") is True


def test_exists_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(region.InvalidRegionNameError):
        region.exists(tmp_path, "bad name!")


def test_read_region_returns_name_and_body(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body text.", "Summary.")

    result = region.read_region(tmp_path, "northlands")

    assert result.name == "northlands"
    assert result.path == ""
    assert result.body.strip() == "Body text."


def test_read_metadata_returns_full_frontmatter_and_body(tmp_path: Path) -> None:
    region.create_region(tmp_path, "frontend", "Body text.", "Summary.", "src/frontend")

    metadata, body = region.read_metadata(tmp_path, "frontend")

    assert metadata["name"] == "frontend"
    assert metadata["path"] == "src/frontend"
    assert body.strip() == "Body text."


def test_read_metadata_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.read_metadata(tmp_path, "missing")


def test_create_region_accepts_path(tmp_path: Path) -> None:
    path = region.create_region(tmp_path, "frontend", "Body.", "Summary.", "src/frontend")

    text = path.read_text(encoding="utf-8")
    assert "path: src/frontend" in text
    assert region.read_region(tmp_path, "frontend").path == "src/frontend"


def test_create_region_stores_summary(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "A routing signal.")

    assert region.read_summary(tmp_path, "northlands") == "A routing signal."


def test_create_region_rejects_over_cap_summary_without_writing(tmp_path: Path) -> None:
    with pytest.raises(region.SummaryTooLongError):
        region.create_region(tmp_path, "northlands", "Body.", "x" * 501)

    assert not region.exists(tmp_path, "northlands")


def test_set_path_updates_path(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    result = region.set_path(tmp_path, "northlands", "src/backend")

    assert result.path == "src/backend"
    assert region.read_region(tmp_path, "northlands").path == "src/backend"


def test_set_path_refreshes_updated_but_not_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    later = datetime(2026, 8, 1, 9, 0, 0, tzinfo=UTC)
    _set_identity(monkeypatch, user="Jane Doe", when=later)
    region.set_path(tmp_path, "northlands", "src/backend")

    metadata, _ = region.read_metadata(tmp_path, "northlands")
    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "Jane Doe"
    assert metadata["updated_on"] == "2026-08-01T09:00:00Z"


def test_set_summary_round_trips(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    region.set_summary(tmp_path, "northlands", "A brief routing signal.")

    assert region.read_summary(tmp_path, "northlands") == "A brief routing signal."


def test_set_summary_refreshes_updated_but_not_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    later = datetime(2026, 8, 1, 9, 0, 0, tzinfo=UTC)
    _set_identity(monkeypatch, user="Jane Doe", when=later)
    region.set_summary(tmp_path, "northlands", "A brief routing signal.")

    metadata, _ = region.read_metadata(tmp_path, "northlands")
    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "Jane Doe"
    assert metadata["updated_on"] == "2026-08-01T09:00:00Z"


def test_set_summary_accepts_value_at_cap(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    region.set_summary(tmp_path, "northlands", "x" * 500)

    assert region.read_summary(tmp_path, "northlands") == "x" * 500


def test_set_summary_rejects_value_over_cap(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    with pytest.raises(region.SummaryTooLongError):
        region.set_summary(tmp_path, "northlands", "x" * 501)


def test_set_summary_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.set_summary(tmp_path, "missing", "text")


def test_read_summary_returns_placeholder_when_absent(tmp_path: Path) -> None:
    # A body written directly without the write-path setter has no summary; the
    # read path must still return the explicit placeholder.
    region_dir = tmp_path / ".sourcebook" / "region"
    region_dir.mkdir(parents=True)
    (region_dir / "northlands.md").write_text("---\nname: northlands\npath: ''\n---\n\nBody.\n", encoding="utf-8")

    assert region.read_summary(tmp_path, "northlands") == frontmatter_utils.SUMMARY_ABSENT_MESSAGE


def test_read_summary_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.read_summary(tmp_path, "missing")


def test_set_summary_preserves_path(tmp_path: Path) -> None:
    region.create_region(tmp_path, "frontend", "Body.", "Summary.", "src/frontend")

    region.set_summary(tmp_path, "frontend", "A brief routing signal.")

    assert region.read_region(tmp_path, "frontend").path == "src/frontend"


def test_set_path_missing_region_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.set_path(tmp_path, "missing", "src/backend")


def test_read_region_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.read_region(tmp_path, "missing")


def test_update_region_replaces_body(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Original.", "Summary.")

    region.update_region(tmp_path, "northlands", "Updated.", "Summary.")

    assert region.read_region(tmp_path, "northlands").body.strip() == "Updated."


def test_update_region_regenerates_summary(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Original.", "Original summary.")

    region.update_region(tmp_path, "northlands", "Updated.", "Updated summary.")

    assert region.read_region(tmp_path, "northlands").body.strip() == "Updated."
    assert region.read_summary(tmp_path, "northlands") == "Updated summary."


def test_update_region_rejects_over_cap_summary_without_writing(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Original.", "Original summary.")

    with pytest.raises(region.SummaryTooLongError):
        region.update_region(tmp_path, "northlands", "Updated.", "x" * 501)

    # Never-stale: the rejected write left the original body and summary intact.
    assert region.read_region(tmp_path, "northlands").body.strip() == "Original."
    assert region.read_summary(tmp_path, "northlands") == "Original summary."


def test_update_region_preserves_path(tmp_path: Path) -> None:
    region.create_region(tmp_path, "frontend", "Original.", "Summary.", "src/frontend")

    region.update_region(tmp_path, "frontend", "Updated.", "Summary.")

    assert region.read_region(tmp_path, "frontend").path == "src/frontend"


def test_update_region_refreshes_updated_but_not_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    region.create_region(tmp_path, "northlands", "Original.", "Summary.")

    later = datetime(2026, 8, 1, 9, 0, 0, tzinfo=UTC)
    _set_identity(monkeypatch, user="Jane Doe", when=later)
    region.update_region(tmp_path, "northlands", "Updated.", "Summary.")

    metadata, _ = region.read_metadata(tmp_path, "northlands")
    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "Jane Doe"
    assert metadata["updated_on"] == "2026-08-01T09:00:00Z"


def test_update_region_propagates_git_identity_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    region.create_region(tmp_path, "northlands", "Original.", "Summary.")

    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        region.update_region(tmp_path, "northlands", "Updated.", "Summary.")

    assert region.read_region(tmp_path, "northlands").body.strip() == "Original."


def test_update_region_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.update_region(tmp_path, "missing", "body", "Summary.")


def test_delete_region_removes_file(tmp_path: Path) -> None:
    path = region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    region.delete_region(tmp_path, "northlands")

    assert not path.exists()


def test_delete_region_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(region.RegionNotFoundError):
        region.delete_region(tmp_path, "missing")


def test_region_path_returns_on_disk_path(tmp_path: Path) -> None:
    assert region.region_path(tmp_path, "northlands") == tmp_path / ".sourcebook" / "region" / "northlands.md"


def test_assign_lore_updates_region_and_lore(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    region.assign_lore(tmp_path, "northlands", "conventions")

    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "conventions" in text
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "northlands" in lore_text
    assert "assigned_regions" in lore_text


def test_assign_lore_refreshes_regions_updated_but_not_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    later = datetime(2026, 8, 1, 9, 0, 0, tzinfo=UTC)
    _set_identity(monkeypatch, user="Jane Doe", when=later)
    region.assign_lore(tmp_path, "northlands", "conventions")

    metadata, _ = region.read_metadata(tmp_path, "northlands")
    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "Jane Doe"
    assert metadata["updated_on"] == "2026-08-01T09:00:00Z"


def test_assign_lore_is_idempotent(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    region.assign_lore(tmp_path, "northlands", "conventions")
    region.assign_lore(tmp_path, "northlands", "conventions")

    text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert text.count("conventions") == 1


def test_assign_lore_missing_region_raises(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    with pytest.raises(region.RegionNotFoundError):
        region.assign_lore(tmp_path, "missing", "conventions")


def test_assign_lore_missing_lore_raises(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    with pytest.raises(lore.LoreNotFoundError):
        region.assign_lore(tmp_path, "northlands", "missing")


def test_lore_can_be_assigned_to_multiple_regions(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    region.create_region(tmp_path, "southlands", "Body.", "Summary.")
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    region.assign_lore(tmp_path, "northlands", "conventions")
    region.assign_lore(tmp_path, "southlands", "conventions")

    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "northlands" in lore_text
    assert "southlands" in lore_text


def test_unassign_lore_updates_region_and_lore(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")
    region.assign_lore(tmp_path, "northlands", "conventions")

    region.unassign_lore(tmp_path, "northlands", "conventions")

    region_text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "conventions" not in region_text
    assert "assigned_regions: []" in lore_text


def test_unassign_lore_missing_region_raises(tmp_path: Path) -> None:
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    with pytest.raises(region.RegionNotFoundError):
        region.unassign_lore(tmp_path, "missing", "conventions")


def test_unassign_lore_missing_lore_raises(tmp_path: Path) -> None:
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    with pytest.raises(lore.LoreNotFoundError):
        region.unassign_lore(tmp_path, "northlands", "missing")
