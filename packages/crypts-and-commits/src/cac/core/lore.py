from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from cac.core import templates
from cac.core.config import LORE_DIR_NAME, NAME_PATTERN
from cac.core.frontmatter_utils import toggle_list_attribute, write_post
from cac.core.paths import sourcebook_dir

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
    if not NAME_PATTERN.fullmatch(name):
        raise InvalidLoreNameError(
            f"Lore name {name!r} is invalid: only letters, numbers, underscores, and hyphens are allowed."
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


def create_lore(root: Path, name: str, body: str) -> Path:
    path = _lore_path(root, name)
    if path.exists():
        raise LoreAlreadyExistsError(f"Lore {name!r} already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME))
    post["name"] = name
    post.content = body
    write_post(path, post)
    return path


def update_lore(root: Path, name: str, body: str) -> Path:
    path = _existing_lore_path(root, name)
    post = frontmatter.load(path)
    post.content = body
    write_post(path, post)
    return path


def delete_lore(root: Path, name: str) -> Path:
    path = _existing_lore_path(root, name)
    path.unlink()
    return path


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
    write_post(path, post)
    return Lore(name=post.get("name", name), body=post.content)


def _set_flag(root: Path, name: str, key: str, value: bool) -> Lore:
    path = _existing_lore_path(root, name)
    post = frontmatter.load(path)
    post[key] = value
    write_post(path, post)
    return Lore(name=post.get("name", name), body=post.content)


def _lore_path(root: Path, name: str) -> Path:
    validate_name(name)
    return lore_dir(root) / f"{name}.md"


def _existing_lore_path(root: Path, name: str) -> Path:
    path = _lore_path(root, name)
    if not path.exists():
        raise LoreNotFoundError(f"Lore {name!r} does not exist.")
    return path
