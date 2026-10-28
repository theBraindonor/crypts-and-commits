"""Standalone backlog rumors: "we think X should be done" notes that planning links to bosses.

The boss link lives only on the rumor; promotion never writes a boss record.
"""

from pathlib import Path
from typing import Any

import frontmatter

from cac.core import boss, frontmatter_utils, templates, world
from cac.core.config import ARCHIVE_DIR_NAME, NAME_PATTERN, RESERVED_NAMES, RUMOR_DIR_NAME, RUMOR_STATUSES
from cac.core.paths import sourcebook_dir

_RESOLVED_STATUSES = ("promoted", "dismissed")
_RENUMBERABLE_STATUSES = ("open", "dismissed")
_HISTORY_KEYS = {"action", "message", "by", "on"}


class RumorError(ValueError):
    """Invalid rumor state, name, input, or storage."""


class RumorNotFoundError(FileNotFoundError):
    """A canonical rumor name has no retained record."""


class RumorAlreadyExistsError(FileExistsError):
    """A name is already retained in live storage or the archive."""


def validate_name(name: str) -> None:
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name) or name in RESERVED_NAMES:
        raise RumorError(f"Invalid rumor name {name!r}: use letters, numbers, underscores, hyphens, or periods.")


def rumor_dir(root: Path, *, archived: bool = False) -> Path:
    base = sourcebook_dir(root)
    return base / ARCHIVE_DIR_NAME / RUMOR_DIR_NAME if archived else base / RUMOR_DIR_NAME


def _locations(root: Path, name: str) -> tuple[Path, Path]:
    validate_name(name)
    return tuple(boss._safe_path(root, rumor_dir(root, archived=a) / f"{name}.md") for a in (False, True))


def rumor_path(root: Path, name: str) -> Path:
    world.read_world(root)
    live, archived = _locations(root, name)
    if live.exists() and archived.exists():
        raise RumorError(f"Rumor {name!r} is ambiguous: both live and archived records exist.")
    if live.exists():
        return live
    if archived.exists():
        return archived
    raise RumorNotFoundError(f"Rumor {name!r} does not exist.")


def _names(root: Path, archived: bool) -> list[str]:
    directory = rumor_dir(root, archived=archived)
    # Validate the directory even if no records match.
    boss._safe_path(root, directory / "_probe.md")
    if not directory.exists():
        return []
    names = []
    for path in sorted(directory.iterdir()):
        if path.suffix == ".md":
            validate_name(path.stem)
            boss._safe_path(root, path)
            names.append(path.stem)
    return names


def list_rumors(root: Path, *, include_archived: bool = False, status: str | None = None) -> list[str]:
    world.read_world(root)
    if status is not None and status not in RUMOR_STATUSES:
        raise RumorError(f"Unknown rumor status {status!r}; valid statuses are: {', '.join(RUMOR_STATUSES)}.")
    live, archived = _names(root, False), _names(root, True)
    overlap = sorted(set(live) & set(archived))
    if overlap:
        raise RumorError(f"Ambiguous live/archive rumor names: {', '.join(overlap)}.")
    names = sorted(live + archived) if include_archived else live
    if status is None:
        return names
    return [name for name in names if _load(root, name)[1]["status"] == status]


def _load(root: Path, name: str) -> tuple[Path, frontmatter.Post]:
    path = rumor_path(root, name)
    post = frontmatter.load(path)
    if post.get("name") != name or post.get("status") not in RUMOR_STATUSES:
        raise RumorError(f"Rumor {name!r} has inconsistent name or invalid status metadata.")
    archived = path.parent == rumor_dir(root, archived=True)
    if type(post.get("archived", False)) is not bool or post.get("archived", False) != archived:
        raise RumorError(f"Rumor {name!r} has an archive flag/location mismatch.")
    linked = post.get("boss")
    if (post["status"] == "promoted") != isinstance(linked, str) or (linked is not None and not linked):
        raise RumorError(f"Rumor {name!r} has boss metadata inconsistent with its status.")
    history = post.get("history", [])
    if not isinstance(history, list) or any(not isinstance(e, dict) or set(e) != _HISTORY_KEYS for e in history):
        raise RumorError(f"Rumor {name!r} has malformed history metadata.")
    return path, post


def read_metadata(root: Path, name: str) -> tuple[dict[str, Any], str]:
    _, post = _load(root, name)
    return dict(post.metadata), post.content


def template_body() -> str:
    return frontmatter.loads(templates.load("sourcebook", "rumor.md")).content


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RumorError(f"A nonblank rumor {label} is required.")
    return value


def _set_fields(post: frontmatter.Post, body: str, summary: str, origin: str) -> None:
    if not isinstance(body, str) or not isinstance(summary, str):
        raise RumorError("Rumor body and summary must be text.")
    post.content = body
    frontmatter_utils.set_summary_attribute(post, _text(summary, "summary"))
    post["origin"] = _text(origin, "origin")


def create_rumor(root: Path, name: str, body: str, summary: str, origin: str) -> Path:
    world.read_world(root)
    live, archived = _locations(root, name)
    if live.exists() or archived.exists():
        raise RumorAlreadyExistsError(f"Rumor {name!r} already exists, live or archived.")
    # Inventory validates directory collisions before any write.
    list_rumors(root, include_archived=True)
    post = frontmatter.loads(templates.load("sourcebook", "rumor.md"))
    post["name"] = name
    _set_fields(post, body, summary, origin)
    frontmatter_utils.stamp_created(post, root)
    live.parent.mkdir(parents=True, exist_ok=True)
    frontmatter_utils.write_post(root, live, post)
    return live


def _editable(post: frontmatter.Post, name: str, statuses: tuple[str, ...]) -> None:
    if post.get("archived", False) or post["status"] not in statuses:
        raise RumorError(f"Rumor {name!r} requires unarchived status in {statuses}; it is {post['status']!r}.")


def _save(root: Path, path: Path, post: frontmatter.Post) -> Path:
    frontmatter_utils.stamp_updated(post, root)
    frontmatter_utils.write_post(root, path, post)
    return path


def update_rumor(root: Path, name: str, body: str, summary: str, origin: str) -> Path:
    path, post = _load(root, name)
    _editable(post, name, ("open",))
    _set_fields(post, body, summary, origin)
    return _save(root, path, post)


def _transition(
    root: Path, name: str, allowed: tuple[str, ...], status: str, action: str, message: str | None, **fields: Any
) -> Path:
    path, post = _load(root, name)
    _editable(post, name, allowed)
    post["status"] = status
    for key, value in fields.items():
        post[key] = value
    user = frontmatter_utils.stamp_updated(post, root)
    post["history"] = [
        *post.get("history", []),
        {"action": action, "message": message, "by": user, "on": post["updated_on"]},
    ]
    frontmatter_utils.write_post(root, path, post)
    return path


def promote(root: Path, name: str, boss_name: str, message: str | None = None) -> Path:
    """Link an open rumor to an existing unassigned proposed/available boss, writing only the rumor."""
    from cac.core import references

    if message is not None and not isinstance(message, str):
        raise RumorError("A promotion message must be text.")
    message = message if message and message.strip() else None
    target = references.Inventory(root).resolve("boss", boss_name)
    metadata, _ = boss.read_metadata(root, target)
    if (
        metadata.get("archived")
        or metadata.get("campaign") is not None
        or metadata["status"]
        not in (
            "proposed",
            "available",
        )
    ):
        raise RumorError(f"Rumors may only be promoted to unassigned proposed/available bosses; {target!r} is not.")
    return _transition(root, name, ("open",), "promoted", "promote", message, boss=target, resolution=message)


def dismiss(root: Path, name: str, message: str) -> Path:
    reason = _text(message, "dismissal reason")
    return _transition(root, name, ("open",), "dismissed", "dismiss", reason, resolution=reason)


def reopen(root: Path, name: str, message: str) -> Path:
    reason = _text(message, "reopen message")
    return _transition(root, name, _RESOLVED_STATUSES, "open", "reopen", reason, boss=None, resolution=None)


def archive_rumor(root: Path, name: str) -> Path:
    from cac.core.recovery import Recovery

    path, post = _load(root, name)
    _editable(post, name, _RESOLVED_STATUSES)
    destination = _locations(root, name)[1]
    if destination.exists():
        raise RumorAlreadyExistsError(f"Archive destination already exists for rumor {name!r}.")
    post["archived"] = True
    frontmatter_utils.stamp_updated(post, root)
    with Recovery(root, [path, destination]):
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Live and archived locations share one index identity, so this write moves the row.
        frontmatter_utils.write_post(root, destination, post)
        path.unlink()
    return destination


def renumber(root: Path, name: str, new_name: str) -> Path:
    """Rename a live open/dismissed rumor; promoted numbers were already settled on planning."""
    from cac.core.recovery import Recovery

    path, post = _load(root, name)
    if post["status"] == "promoted":
        raise RumorError(f"Rumor {name!r} is promoted; its number is settled. Reopen it before renumbering.")
    _editable(post, name, _RENUMBERABLE_STATUSES)
    live, archived = _locations(root, new_name)
    if live.exists() or archived.exists():
        raise RumorAlreadyExistsError(f"Rumor {new_name!r} already exists, live or archived.")
    list_rumors(root, include_archived=True)
    post["name"] = new_name
    frontmatter_utils.stamp_updated(post, root)
    with Recovery(root, [path, live]):
        frontmatter_utils.write_post(root, live, post)
        frontmatter_utils.delete_post(root, path)
    return live


def get_payload(root: Path, name: str) -> dict[str, Any]:
    """The unbudgeted rumor_get result shared by CLI and MCP, before identity and budget fitting."""
    metadata, body = read_metadata(root, name)
    summary = metadata.pop("summary", "")
    return {"metadata": metadata, "summary": summary, "body": body}
