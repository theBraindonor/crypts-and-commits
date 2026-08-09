from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cac.core import git_utils, lore, world


def test_initialize_world_creates_file_from_template(tmp_path: Path) -> None:
    path, created = world.initialize_world(tmp_path)

    assert created is True
    assert path == tmp_path / ".sourcebook" / "world.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name:" in text


def test_initialize_world_is_idempotent(tmp_path: Path) -> None:
    path, _ = world.initialize_world(tmp_path)
    path.write_text("---\nname: keep-me\n---\n\nCustom body.\n", encoding="utf-8")

    _, created = world.initialize_world(tmp_path)

    assert created is False
    assert "keep-me" in path.read_text(encoding="utf-8")


def test_initialize_world_sets_created_and_updated_fields(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = world.read_world(tmp_path)

    assert result.metadata["created_by"] == "John Hoff"
    assert result.metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert result.metadata["updated_by"] == "John Hoff"
    assert result.metadata["updated_on"] == "2026-07-23T18:04:12Z"


def test_initialize_world_propagates_git_identity_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        world.initialize_world(tmp_path)

    assert not world.world_path(tmp_path).exists()


def test_read_world_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
        world.read_world(tmp_path)


def test_read_world_returns_metadata_and_body(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = world.read_world(tmp_path)

    assert result.metadata == {
        "name": "unnamed_world",
        "assigned_lore": [],
        "schema_version": 1,
        "created_by": "John Hoff",
        "created_on": "2026-07-23T18:04:12Z",
        "updated_by": "John Hoff",
        "updated_on": "2026-07-23T18:04:12Z",
    }
    assert "Be sure to edit this world definition file before starting development!" in result.body


def test_set_attribute_updates_metadata(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = world.set_attribute(tmp_path, "name", "my-project")

    assert result.metadata["name"] == "my-project"
    assert world.read_world(tmp_path).metadata["name"] == "my-project"


def test_set_attribute_refreshes_updated_but_not_created(tmp_path: Path, identity: Callable[..., None]) -> None:
    world.initialize_world(tmp_path)

    later = datetime(2026, 8, 1, 9, 0, 0, tzinfo=UTC)
    identity(user="Jane Doe", when=later)
    world.set_attribute(tmp_path, "name", "my-project")

    metadata = world.read_world(tmp_path).metadata
    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "Jane Doe"
    assert metadata["updated_on"] == "2026-08-01T09:00:00Z"


def test_set_attribute_missing_world_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
        world.set_attribute(tmp_path, "name", "my-project")


def test_set_attribute_propagates_git_identity_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world.initialize_world(tmp_path)

    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        world.set_attribute(tmp_path, "name", "my-project")


def test_update_body_replaces_content(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = world.update_body(tmp_path, "New content.")

    assert result.body.strip() == "New content."
    assert world.read_world(tmp_path).body.strip() == "New content."


def test_update_body_preserves_metadata(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    world.set_attribute(tmp_path, "name", "my-project")

    world.update_body(tmp_path, "New content.")

    assert world.read_world(tmp_path).metadata["name"] == "my-project"


def test_update_body_refreshes_updated_but_not_created(tmp_path: Path, identity: Callable[..., None]) -> None:
    world.initialize_world(tmp_path)

    later = datetime(2026, 8, 1, 9, 0, 0, tzinfo=UTC)
    identity(user="Jane Doe", when=later)
    world.update_body(tmp_path, "New content.")

    metadata = world.read_world(tmp_path).metadata
    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "Jane Doe"
    assert metadata["updated_on"] == "2026-08-01T09:00:00Z"


def test_update_body_missing_world_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
        world.update_body(tmp_path, "New content.")


def test_update_body_propagates_git_identity_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world.initialize_world(tmp_path)

    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        world.update_body(tmp_path, "New content.")


def test_assign_lore_updates_world_and_lore(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    result = world.assign_lore(tmp_path, "conventions")

    assert result.metadata["assigned_lore"] == ["conventions"]
    assert lore.read_lore(tmp_path, "conventions").name == "conventions"
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "assigned_to_world: true" in lore_text


def test_assign_lore_refreshes_worlds_updated_but_not_created(tmp_path: Path, identity: Callable[..., None]) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    later = datetime(2026, 8, 1, 9, 0, 0, tzinfo=UTC)
    identity(user="Jane Doe", when=later)
    world.assign_lore(tmp_path, "conventions")

    metadata = world.read_world(tmp_path).metadata
    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "Jane Doe"
    assert metadata["updated_on"] == "2026-08-01T09:00:00Z"


def test_assign_lore_is_idempotent(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    world.assign_lore(tmp_path, "conventions")
    result = world.assign_lore(tmp_path, "conventions")

    assert result.metadata["assigned_lore"] == ["conventions"]


def test_assign_lore_missing_world_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
        world.assign_lore(tmp_path, "conventions")


def test_assign_lore_missing_lore_raises(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    with pytest.raises(lore.LoreNotFoundError):
        world.assign_lore(tmp_path, "missing")


def test_assign_lore_propagates_git_identity_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")

    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        world.assign_lore(tmp_path, "conventions")


def test_unassign_lore_updates_world_and_lore(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "conventions", "Body.", "Summary.")
    world.assign_lore(tmp_path, "conventions")

    result = world.unassign_lore(tmp_path, "conventions")

    assert result.metadata["assigned_lore"] == []
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "assigned_to_world: false" in lore_text


def test_unassign_lore_missing_world_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
        world.unassign_lore(tmp_path, "conventions")


def test_unassign_lore_missing_lore_raises(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    with pytest.raises(lore.LoreNotFoundError):
        world.unassign_lore(tmp_path, "missing")


def test_initialize_world_stamps_current_schema_version(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    assert world.read_world(tmp_path).metadata["schema_version"] == world.SOURCEBOOK_SCHEMA_VERSION


def test_check_schema_version_missing_world_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
        world.check_schema_version(tmp_path)


def test_check_schema_version_current(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    status = world.check_schema_version(tmp_path)

    assert status == world.SchemaVersionStatus(
        stored=world.SOURCEBOOK_SCHEMA_VERSION,
        current=world.SOURCEBOOK_SCHEMA_VERSION,
        outcome=world.SCHEMA_VERSION_OUTCOME_CURRENT,
    )


def test_check_schema_version_missing_attribute_implies_version_one(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    path = world.world_path(tmp_path)
    path.write_text(path.read_text(encoding="utf-8").replace("schema_version: 1\n", ""), encoding="utf-8")

    status = world.check_schema_version(tmp_path)

    assert status.stored == 1


def test_check_schema_version_behind(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world.initialize_world(tmp_path)
    monkeypatch.setattr(world, "SOURCEBOOK_SCHEMA_VERSION", 2)

    status = world.check_schema_version(tmp_path)

    assert status.outcome == world.SCHEMA_VERSION_OUTCOME_BEHIND
    assert status.stored == 1
    assert status.current == 2


def test_check_schema_version_ahead(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    world.set_attribute(tmp_path, "schema_version", "2")

    status = world.check_schema_version(tmp_path)

    assert status.outcome == world.SCHEMA_VERSION_OUTCOME_AHEAD
    assert status.stored == 2
    assert status.current == 1


def test_check_schema_version_never_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world.initialize_world(tmp_path)
    monkeypatch.setattr(world, "SOURCEBOOK_SCHEMA_VERSION", 2)
    path = world.world_path(tmp_path)
    before = path.read_text(encoding="utf-8")

    world.check_schema_version(tmp_path)

    assert path.read_text(encoding="utf-8") == before
