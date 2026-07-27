from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from cac.core import frontmatter_utils, templates
from cac.core import lore as lore_core
from cac.core.config import WORLD_FILE_NAME
from cac.core.frontmatter_utils import toggle_list_attribute, write_post
from cac.core.paths import sourcebook_dir

_TEMPLATE_PACKAGE = "sourcebook"
_TEMPLATE_FILENAME = "world.md"
ASSIGNED_LORE_KEY = "assigned_lore"


class WorldNotFoundError(FileNotFoundError):
    """Raised when the world file does not exist."""


@dataclass(frozen=True)
class World:
    metadata: dict[str, Any]
    body: str


def world_path(root: Path) -> Path:
    return sourcebook_dir(root) / WORLD_FILE_NAME


def initialize_world(root: Path) -> tuple[Path, bool]:
    """Create world.md from the packaged template if it doesn't already exist."""
    path = world_path(root)
    created = not path.exists()
    if created:
        path.parent.mkdir(parents=True, exist_ok=True)
        post = frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME))
        frontmatter_utils.stamp_created(post, root)
        write_post(root, path, post)
    return path, created


def read_world(root: Path) -> World:
    post = frontmatter.load(_existing_world_path(root))
    return World(metadata=dict(post.metadata), body=post.content)


def set_attribute(root: Path, key: str, value: str) -> World:
    path = _existing_world_path(root)
    post = frontmatter.load(path)
    post[key] = value
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return World(metadata=dict(post.metadata), body=post.content)


def update_body(root: Path, body: str) -> World:
    path = _existing_world_path(root)
    post = frontmatter.load(path)
    post.content = body
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return World(metadata=dict(post.metadata), body=post.content)


def assign_lore(root: Path, name: str) -> World:
    """Assign a lore file to the world, recording the link on both sides."""
    _existing_world_path(root)
    if not lore_core.exists(root, name):
        raise lore_core.LoreNotFoundError(f"Lore {name!r} does not exist.")
    lore_core.set_assigned_to_world(root, name, True)
    return _update_assigned_lore(root, add=name)


def unassign_lore(root: Path, name: str) -> World:
    """Unassign a lore file from the world, clearing the link on both sides."""
    _existing_world_path(root)
    if not lore_core.exists(root, name):
        raise lore_core.LoreNotFoundError(f"Lore {name!r} does not exist.")
    lore_core.set_assigned_to_world(root, name, False)
    return _update_assigned_lore(root, remove=name)


def _update_assigned_lore(root: Path, *, add: str | None = None, remove: str | None = None) -> World:
    path = _existing_world_path(root)
    post = frontmatter.load(path)
    toggle_list_attribute(post, ASSIGNED_LORE_KEY, add=add, remove=remove)
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return World(metadata=dict(post.metadata), body=post.content)


def _existing_world_path(root: Path) -> Path:
    path = world_path(root)
    if not path.exists():
        raise WorldNotFoundError("world.md does not exist. Run 'cac bootstrap init' first.")
    return path
