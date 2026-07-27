from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from cac.core import frontmatter_utils, templates
from cac.core.config import LORE_DIR_NAME, NAME_PATTERN, RESERVED_NAMES
from cac.core.frontmatter_utils import (
    SummaryTooLongError,
    set_summary_attribute,
    summary_or_placeholder,
    toggle_list_attribute,
    write_post,
)
from cac.core.paths import sourcebook_dir

__all__ = ["SummaryTooLongError"]  # re-exported so the CLI can catch it alongside lore errors

_TEMPLATE_PACKAGE = "sourcebook"
_TEMPLATE_FILENAME = "lore.md"
ASSIGNED_REGIONS_KEY = "assigned_regions"


class InvalidLoreNameError(ValueError):
    """Raised when a lore name contains characters other than letters, numbers, underscores, and hyphens."""


class LoreNotFoundError(FileNotFoundError):
    """Raised when a named lore file does not exist."""


class LoreAlreadyExistsError(FileExistsError):
    """Raised when a named lore file already exists."""


@dataclass(frozen=True)
class Lore:
    name: str
    body: str


def lore_dir(root: Path) -> Path:
    return sourcebook_dir(root) / LORE_DIR_NAME


def validate_name(name: str) -> None:
    if not NAME_PATTERN.fullmatch(name) or name in RESERVED_NAMES:
        raise InvalidLoreNameError(
            f"Lore name {name!r} is invalid: only letters, numbers, underscores, hyphens, and periods are allowed "
            "(and the name cannot be '.' or '..')."
        )


def exists(root: Path, name: str) -> bool:
    validate_name(name)
    return (lore_dir(root) / f"{name}.md").exists()


def list_lore(root: Path) -> list[str]:
    directory = lore_dir(root)
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*.md"))


def template_body() -> str:
    return frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME)).content


def read_lore(root: Path, name: str) -> Lore:
    post = frontmatter.load(_existing_lore_path(root, name))
    return Lore(name=post.get("name", name), body=post.content)


def read_metadata(root: Path, name: str) -> tuple[dict[str, Any], str]:
    post = frontmatter.load(_existing_lore_path(root, name))
    return dict(post.metadata), post.content


def create_lore(root: Path, name: str, body: str, summary: str) -> Path:
    """Create a lore file, writing the body and its summary together.

    The summary is a required companion of the body write (enforced within the
    length cap) so a body can never be stored without a current summary.
    """
    path = _lore_path(root, name)
    if path.exists():
        raise LoreAlreadyExistsError(f"Lore {name!r} already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME))
    post["name"] = name
    post.content = body
    set_summary_attribute(post, summary)
    frontmatter_utils.stamp_created(post, root)
    write_post(root, path, post)
    return path


def update_lore(root: Path, name: str, body: str, summary: str) -> Path:
    """Replace a lore file's body, regenerating its summary in the same write.

    The summary is required so an edited body cannot commit without an
    accompanying current summary; an over-cap summary aborts the write before
    anything is persisted.
    """
    path = _existing_lore_path(root, name)
    post = frontmatter.load(path)
    post.content = body
    set_summary_attribute(post, summary)
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return path


def delete_lore(root: Path, name: str) -> Path:
    path = _existing_lore_path(root, name)
    return frontmatter_utils.delete_post(root, path)


def set_summary(root: Path, name: str, summary: str) -> Lore:
    """Set this lore's summary, rejecting a value over the length cap."""
    path = _existing_lore_path(root, name)
    post = frontmatter.load(path)
    set_summary_attribute(post, summary)
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return Lore(name=post.get("name", name), body=post.content)


def read_summary(root: Path, name: str) -> str:
    """Return this lore's stored summary, or a placeholder message when none is set."""
    post = frontmatter.load(_existing_lore_path(root, name))
    return summary_or_placeholder(post)


def lore_path(root: Path, name: str) -> Path:
    """Return the on-disk path for a lore entry, e.g. for use in a truncation fallback notice."""
    return _lore_path(root, name)


def set_enabled(root: Path, name: str, enabled: bool) -> Lore:
    return _set_flag(root, name, "enabled", enabled)


def set_assigned_to_world(root: Path, name: str, assigned: bool) -> Lore:
    return _set_flag(root, name, "assigned_to_world", assigned)


def add_assigned_region(root: Path, name: str, region: str) -> Lore:
    return _update_assigned_regions(root, name, add=region)


def remove_assigned_region(root: Path, name: str, region: str) -> Lore:
    return _update_assigned_regions(root, name, remove=region)


def _update_assigned_regions(root: Path, name: str, *, add: str | None = None, remove: str | None = None) -> Lore:
    path = _existing_lore_path(root, name)
    post = frontmatter.load(path)
    toggle_list_attribute(post, ASSIGNED_REGIONS_KEY, add=add, remove=remove)
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return Lore(name=post.get("name", name), body=post.content)


def _set_flag(root: Path, name: str, key: str, value: bool) -> Lore:
    path = _existing_lore_path(root, name)
    post = frontmatter.load(path)
    post[key] = value
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return Lore(name=post.get("name", name), body=post.content)


def _lore_path(root: Path, name: str) -> Path:
    validate_name(name)
    return lore_dir(root) / f"{name}.md"


def _existing_lore_path(root: Path, name: str) -> Path:
    path = _lore_path(root, name)
    if not path.exists():
        raise LoreNotFoundError(f"Lore {name!r} does not exist.")
    return path
