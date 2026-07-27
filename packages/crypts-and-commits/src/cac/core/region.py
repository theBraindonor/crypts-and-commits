from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from cac.core import frontmatter_utils, templates
from cac.core import lore as lore_core
from cac.core.config import NAME_PATTERN, REGION_DIR_NAME, RESERVED_NAMES
from cac.core.frontmatter_utils import (
    SummaryTooLongError,
    set_summary_attribute,
    summary_or_placeholder,
    toggle_list_attribute,
    write_post,
)
from cac.core.paths import sourcebook_dir

__all__ = ["SummaryTooLongError"]  # re-exported so the CLI can catch it alongside region errors

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
    if not NAME_PATTERN.fullmatch(name) or name in RESERVED_NAMES:
        raise InvalidRegionNameError(
            f"Region name {name!r} is invalid: only letters, numbers, underscores, hyphens, and periods are "
            "allowed (and the name cannot be '.' or '..')."
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


def create_region(root: Path, name: str, body: str, summary: str, path_value: str = "") -> Path:
    """Create a region file, writing the body and its summary together.

    The summary is a required companion of the body write (enforced within the
    length cap) so a body can never be stored without a current summary.
    """
    path = _region_path(root, name)
    if path.exists():
        raise RegionAlreadyExistsError(f"Region {name!r} already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME))
    post["name"] = name
    post["path"] = path_value
    post.content = body
    set_summary_attribute(post, summary)
    frontmatter_utils.stamp_created(post, root)
    write_post(root, path, post)
    return path


def update_region(root: Path, name: str, body: str, summary: str) -> Path:
    """Replace a region's body, regenerating its summary in the same write.

    The summary is required so an edited body cannot commit without an
    accompanying current summary; an over-cap summary aborts the write before
    anything is persisted.
    """
    path = _existing_region_path(root, name)
    post = frontmatter.load(path)
    post.content = body
    set_summary_attribute(post, summary)
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return path


def delete_region(root: Path, name: str) -> Path:
    path = _existing_region_path(root, name)
    return frontmatter_utils.delete_post(root, path)


def set_summary(root: Path, name: str, summary: str) -> Region:
    """Set this region's summary, rejecting a value over the length cap."""
    path = _existing_region_path(root, name)
    post = frontmatter.load(path)
    set_summary_attribute(post, summary)
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return _to_region(post, name)


def read_summary(root: Path, name: str) -> str:
    """Return this region's stored summary, or a placeholder message when none is set."""
    post = frontmatter.load(_existing_region_path(root, name))
    return summary_or_placeholder(post)


def region_path(root: Path, name: str) -> Path:
    """Return the on-disk path for a region entry, e.g. for use in a truncation fallback notice."""
    return _region_path(root, name)


def set_path(root: Path, name: str, path_value: str) -> Region:
    path = _existing_region_path(root, name)
    post = frontmatter.load(path)
    post["path"] = path_value
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
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
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
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
