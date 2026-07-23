from pathlib import Path

import pytest

from cac.core import lore, world


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


def test_read_world_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
        world.read_world(tmp_path)


def test_read_world_returns_metadata_and_body(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = world.read_world(tmp_path)

    assert result.metadata == {"name": "unnamed_world"}
    assert "Be sure to edit this world definition file before starting development!" in result.body


def test_set_attribute_updates_metadata(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)

    result = world.set_attribute(tmp_path, "name", "my-project")

    assert result.metadata["name"] == "my-project"
    assert world.read_world(tmp_path).metadata["name"] == "my-project"


def test_set_attribute_missing_world_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
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


def test_update_body_missing_world_raises(tmp_path: Path) -> None:
    with pytest.raises(world.WorldNotFoundError):
        world.update_body(tmp_path, "New content.")


def test_assign_lore_updates_world_and_lore(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "conventions", "Body.")

    result = world.assign_lore(tmp_path, "conventions")

    assert result.metadata["assigned_lore"] == ["conventions"]
    assert lore.read_lore(tmp_path, "conventions").name == "conventions"
    lore_text = (tmp_path / ".sourcebook" / "lore" / "conventions.md").read_text(encoding="utf-8")
    assert "assigned_to_world: true" in lore_text


def test_assign_lore_is_idempotent(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "conventions", "Body.")

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


def test_unassign_lore_updates_world_and_lore(tmp_path: Path) -> None:
    world.initialize_world(tmp_path)
    lore.create_lore(tmp_path, "conventions", "Body.")
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
