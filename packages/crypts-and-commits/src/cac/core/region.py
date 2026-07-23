from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from cac.core import lore as lore_core
from cac.core import templates
from cac.core.config import NAME_PATTERN, REGION_DIR_NAME
from cac.core.frontmatter_utils import toggle_list_attribute, write_post
from cac.core.paths import sourcebook_dir

_TEMPLATE_PACKAGE = "sourcebook"
_TEMPLATE_FILENAME = "region.md"
ASSIGNED_LORE_KEY = "assigned_lore"


class InvalidRegionNameError(ValueError):
    """Raised when a region name contains characters other than letters, numbers, underscores, and hyphens."""


class RegionNotFoundError(FileNotFoundError):
    """Raised when a named region file does not exist."""


class RegionAlreadyExistsError(FileExistsError):
    """Raised when a named region file already exists."""


@dataclass(frozen=True)
class Region:
    name: str
    path: str
    body: str


def region_dir(root: Path) -> Path:
    return sourcebook_dir(root) / REGION_DIR_NAME


def validate_name(name: str) -> None:
    if not NAME_PATTERN.fullmatch(name):
        raise InvalidRegionNameError(
            f"Region name {name!r} is invalid: only letters, numbers, underscores, and hyphens are allowed."
        )


def exists(root: Path, name: str) -> bool:
    validate_name(name)
    return (region_dir(root) / f"{name}.md").exists()


def list_regions(root: Path) -> list[str]:
    directory = region_dir(root)
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*.md"))


def template_body() -> str:
    return frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME)).content


def read_region(root: Path, name: str) -> Region:
    post = frontmatter.load(_existing_region_path(root, name))
    return _to_region(post, name)


def read_metadata(root: Path, name: str) -> tuple[dict[str, Any], str]:
    post = frontmatter.load(_existing_region_path(root, name))
    return dict(post.metadata), post.content


def create_region(root: Path, name: str, body: str, path_value: str = "") -> Path:
    path = _region_path(root, name)
    if path.exists():
        raise RegionAlreadyExistsError(f"Region {name!r} already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME))
    post["name"] = name
    post["path"] = path_value
    post.content = body
    write_post(path, post)
    return path


def update_region(root: Path, name: str, body: str) -> Path:
    path = _existing_region_path(root, name)
    post = frontmatter.load(path)
    post.content = body
    write_post(path, post)
    return path


def delete_region(root: Path, name: str) -> Path:
    path = _existing_region_path(root, name)
    path.unlink()
    return path


def set_path(root: Path, name: str, path_value: str) -> Region:
    path = _existing_region_path(root, name)
    post = frontmatter.load(path)
    post["path"] = path_value
    write_post(path, post)
    return _to_region(post, name)


def assign_lore(root: Path, region_name: str, lore_name: str) -> Region:
    """Assign a lore file to this region, recording the link on both sides."""
    _existing_region_path(root, region_name)
    if not lore_core.exists(root, lore_name):
        raise lore_core.LoreNotFoundError(f"Lore {lore_name!r} does not exist.")
    lore_core.add_assigned_region(root, lore_name, region_name)
    return _update_assigned_lore(root, region_name, add=lore_name)


def unassign_lore(root: Path, region_name: str, lore_name: str) -> Region:
    """Unassign a lore file from this region, clearing the link on both sides."""
    _existing_region_path(root, region_name)
    if not lore_core.exists(root, lore_name):
        raise lore_core.LoreNotFoundError(f"Lore {lore_name!r} does not exist.")
    lore_core.remove_assigned_region(root, lore_name, region_name)
    return _update_assigned_lore(root, region_name, remove=lore_name)


def _update_assigned_lore(root: Path, region_name: str, *, add: str | None = None, remove: str | None = None) -> Region:
    path = _existing_region_path(root, region_name)
    post = frontmatter.load(path)
    toggle_list_attribute(post, ASSIGNED_LORE_KEY, add=add, remove=remove)
    write_post(path, post)
    return _to_region(post, region_name)


def _to_region(post: frontmatter.Post, name: str) -> Region:
    return Region(
        name=post.get("name", name),
        path=post.get("path", ""),
        body=post.content,
    )


def _region_path(root: Path, name: str) -> Path:
    validate_name(name)
    return region_dir(root) / f"{name}.md"


def _existing_region_path(root: Path, name: str) -> Path:
    path = _region_path(root, name)
    if not path.exists():
        raise RegionNotFoundError(f"Region {name!r} does not exist.")
    return path
