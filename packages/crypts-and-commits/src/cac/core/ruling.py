"""Rulings: developer (GM) decisions recorded during active development, triaged on planning.

A ruling's name, ``cNNN-eNNN-slug``, ties it to the campaign and encounter (``e000`` for none)
where the decision was made. That link lives only on the ruling: campaign and encounter records
are never written. The open-campaign capture guard applies at creation only; later edits and
dispositions happen in hindsight, usually after the campaign completed.
"""

from pathlib import Path
from typing import Any

import frontmatter

from cac.core import boss, frontmatter_utils, templates, world
from cac.core.config import (
    ARCHIVE_DIR_NAME,
    NUMBERED_NAME_PATTERN,
    RESERVED_NAMES,
    RULING_DIR_NAME,
    RULING_NAME_PATTERN,
    RULING_STATUSES,
)
from cac.core.paths import sourcebook_dir

_RESOLVED_STATUSES = ("canonized", "noted")
_HISTORY_KEYS = {"action", "message", "by", "on"}
_NO_ENCOUNTER = 0


class RulingError(ValueError):
    """Invalid ruling state, name, input, or storage."""


class RulingNotFoundError(FileNotFoundError):
    """A canonical ruling name has no retained record."""


class RulingAlreadyExistsError(FileExistsError):
    """A name is already retained in live storage or the archive."""


def parse_name(name: str) -> tuple[int, int, str]:
    """Return (campaign number, encounter number, slug); encounter number 0 means no encounter."""
    match = RULING_NAME_PATTERN.fullmatch(name) if isinstance(name, str) else None
    if not match or name in RESERVED_NAMES:
        raise RulingError(
            f"Invalid ruling name {name!r}: use cNNN-eNNN-slug (e000 when no encounter is open), with a slug "
            "of letters, numbers, underscores, hyphens, or periods."
        )
    if int(match[1]) == 0:
        raise RulingError(f"Invalid ruling name {name!r}: the campaign number must be positive.")
    return int(match[1]), int(match[2]), match[3]


def validate_name(name: str) -> None:
    parse_name(name)


def ruling_dir(root: Path, *, archived: bool = False) -> Path:
    base = sourcebook_dir(root)
    return base / ARCHIVE_DIR_NAME / RULING_DIR_NAME if archived else base / RULING_DIR_NAME


def _locations(root: Path, name: str) -> tuple[Path, Path]:
    validate_name(name)
    return tuple(boss._safe_path(root, ruling_dir(root, archived=a) / f"{name}.md") for a in (False, True))


def ruling_path(root: Path, name: str) -> Path:
    world.read_world(root)
    live, archived = _locations(root, name)
    if live.exists() and archived.exists():
        raise RulingError(f"Ruling {name!r} is ambiguous: both live and archived records exist.")
    if live.exists():
        return live
    if archived.exists():
        return archived
    raise RulingNotFoundError(f"Ruling {name!r} does not exist.")


def _names(root: Path, archived: bool) -> list[str]:
    directory = ruling_dir(root, archived=archived)
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


def list_rulings(root: Path, *, include_archived: bool = False, status: str | None = None) -> list[str]:
    world.read_world(root)
    if status is not None and status not in RULING_STATUSES:
        raise RulingError(f"Unknown ruling status {status!r}; valid statuses are: {', '.join(RULING_STATUSES)}.")
    live, archived = _names(root, False), _names(root, True)
    overlap = sorted(set(live) & set(archived))
    if overlap:
        raise RulingError(f"Ambiguous live/archive ruling names: {', '.join(overlap)}.")
    names = sorted(live + archived) if include_archived else live
    if status is None:
        return names
    return [name for name in names if _load(root, name)[1]["status"] == status]


def _number(value: Any, prefix: str) -> int | None:
    match = NUMBERED_NAME_PATTERN.fullmatch(value) if isinstance(value, str) else None
    return int(match[2]) if match and match[1] == prefix else None


def _load(root: Path, name: str) -> tuple[Path, frontmatter.Post]:
    """Load and validate a ruling from its own metadata only, so it stays readable after its
    campaign or encounter has been archived."""
    path = ruling_path(root, name)
    post = frontmatter.load(path)
    if post.get("name") != name or post.get("status") not in RULING_STATUSES:
        raise RulingError(f"Ruling {name!r} has inconsistent name or invalid status metadata.")
    archived = path.parent == ruling_dir(root, archived=True)
    if type(post.get("archived", False)) is not bool or post.get("archived", False) != archived:
        raise RulingError(f"Ruling {name!r} has an archive flag/location mismatch.")
    campaign_number, encounter_number, _ = parse_name(name)
    encounter_name = post.get("encounter")
    if _number(post.get("campaign"), "c") != campaign_number or (
        _number(encounter_name, "e") != encounter_number
        if encounter_number != _NO_ENCOUNTER
        else encounter_name is not None
    ):
        raise RulingError(f"Ruling {name!r} has campaign/encounter metadata inconsistent with its name.")
    resolution = post.get("resolution")
    resolved = post["status"] in _RESOLVED_STATUSES
    if resolved != (isinstance(resolution, str) and bool(resolution.strip())) or (not resolved and resolution):
        raise RulingError(f"Ruling {name!r} has resolution metadata inconsistent with its status.")
    history = post.get("history", [])
    if not isinstance(history, list) or any(not isinstance(e, dict) or set(e) != _HISTORY_KEYS for e in history):
        raise RulingError(f"Ruling {name!r} has malformed history metadata.")
    return path, post


def read_metadata(root: Path, name: str) -> tuple[dict[str, Any], str]:
    _, post = _load(root, name)
    return dict(post.metadata), post.content


def template_body() -> str:
    return frontmatter.loads(templates.load("sourcebook", "ruling.md")).content


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RulingError(f"A nonblank ruling {label} is required.")
    return value


def _set_fields(post: frontmatter.Post, body: str, summary: str, origin: str) -> None:
    if not isinstance(body, str) or not isinstance(summary, str):
        raise RulingError("Ruling body and summary must be text.")
    post.content = body
    frontmatter_utils.set_summary_attribute(post, _text(summary, "summary"))
    post["origin"] = _text(origin, "origin")


def _capture_context(root: Path, name: str) -> tuple[str, str | None]:
    """Resolve the name's campaign/encounter numbers; the campaign must be open right now."""
    from cac.core import campaign, references

    campaign_number, encounter_number, _ = parse_name(name)
    inventory = references.Inventory(root)
    campaign_name = inventory.resolve("campaign", f"c{campaign_number:03d}")
    status = campaign.read_metadata(root, campaign_name)[0].get("status")
    if status != "open":
        raise RulingError(
            f"Cannot record ruling {name!r}: campaign {campaign_name!r} is {status!r}, and rulings are only "
            "captured during an open campaign. Capture the decision as a rumor instead."
        )
    if encounter_number == _NO_ENCOUNTER:
        return campaign_name, None
    return campaign_name, inventory.resolve("encounter", f"e{encounter_number:03d}", campaign_name)


def create_ruling(root: Path, name: str, body: str, summary: str, origin: str) -> Path:
    world.read_world(root)
    live, archived = _locations(root, name)
    if live.exists() or archived.exists():
        raise RulingAlreadyExistsError(f"Ruling {name!r} already exists, live or archived.")
    # Inventory validates directory collisions before any write.
    list_rulings(root, include_archived=True)
    campaign_name, encounter_name = _capture_context(root, name)
    post = frontmatter.loads(templates.load("sourcebook", "ruling.md"))
    post["name"] = name
    post["campaign"] = campaign_name
    post["encounter"] = encounter_name
    _set_fields(post, body, summary, origin)
    frontmatter_utils.stamp_created(post, root)
    live.parent.mkdir(parents=True, exist_ok=True)
    frontmatter_utils.write_post(root, live, post)
    return live


def _editable(post: frontmatter.Post, name: str, statuses: tuple[str, ...]) -> None:
    if post.get("archived", False) or post["status"] not in statuses:
        raise RulingError(f"Ruling {name!r} requires unarchived status in {statuses}; it is {post['status']!r}.")


def update_ruling(root: Path, name: str, body: str, summary: str, origin: str) -> Path:
    path, post = _load(root, name)
    _editable(post, name, ("recorded",))
    _set_fields(post, body, summary, origin)
    frontmatter_utils.stamp_updated(post, root)
    frontmatter_utils.write_post(root, path, post)
    return path


def _transition(
    root: Path, name: str, allowed: tuple[str, ...], status: str, action: str, message: str, resolution: str | None
) -> Path:
    path, post = _load(root, name)
    _editable(post, name, allowed)
    post["status"] = status
    post["resolution"] = resolution
    user = frontmatter_utils.stamp_updated(post, root)
    post["history"] = [
        *post.get("history", []),
        {"action": action, "message": message, "by": user, "on": post["updated_on"]},
    ]
    frontmatter_utils.write_post(root, path, post)
    return path


def canonize(root: Path, name: str, message: str) -> Path:
    """Record that the world (lore, regions, world summary) was updated to reflect this ruling."""
    narrative = _text(message, "canonization narrative")
    return _transition(root, name, ("recorded",), "canonized", "canonize", narrative, narrative)


def note(root: Path, name: str, message: str) -> Path:
    """Record why this ruling needs no world update."""
    narrative = _text(message, "noting narrative")
    return _transition(root, name, ("recorded",), "noted", "note", narrative, narrative)


def reopen(root: Path, name: str, message: str) -> Path:
    reason = _text(message, "reopen message")
    return _transition(root, name, _RESOLVED_STATUSES, "recorded", "reopen", reason, None)


def archive_ruling(root: Path, name: str) -> Path:
    from cac.core.recovery import Recovery

    path, post = _load(root, name)
    _editable(post, name, _RESOLVED_STATUSES)
    destination = _locations(root, name)[1]
    if destination.exists():
        raise RulingAlreadyExistsError(f"Archive destination already exists for ruling {name!r}.")
    post["archived"] = True
    frontmatter_utils.stamp_updated(post, root)
    with Recovery(root, [path, destination]):
        destination.parent.mkdir(parents=True, exist_ok=True)
        frontmatter_utils.write_post(root, destination, post)
        path.unlink()
    return destination


def get_payload(root: Path, name: str) -> dict[str, Any]:
    """The unbudgeted ruling_get result shared by CLI and MCP, before identity and budget fitting."""
    metadata, body = read_metadata(root, name)
    summary = metadata.pop("summary", "")
    return {"metadata": metadata, "summary": summary, "body": body}
