from pathlib import Path

import pytest
from cac.core import git_utils, world
from cac.mcp import world as mcp_world


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def _default_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(git_utils, "current_git_user", lambda root: "John Hoff")


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
