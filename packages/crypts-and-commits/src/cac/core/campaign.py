from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from cac.core import frontmatter_utils, templates
from cac.core.config import (
    ARCHIVE_DIR_NAME,
    ARCHIVED_KEY,
    CAMPAIGN_DIR_NAME,
    DEFAULT_CAMPAIGN_STATUS,
    DEFAULT_ENCOUNTER_STATUS,
    ENCOUNTER_DIR_NAME,
    NAME_PATTERN,
    RESERVED_NAMES,
)
from cac.core.frontmatter_utils import write_post
from cac.core.paths import sourcebook_dir

_TEMPLATE_PACKAGE = "sourcebook"
_TEMPLATE_FILENAME = "campaign.md"
_LOG_SECTION = "Log"

_CAMPAIGN_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"open", "abandoned"}),
    "open": frozenset({"paused", "completed", "abandoned"}),
    "paused": frozenset({"open", "completed", "abandoned"}),
    "completed": frozenset(),
    "abandoned": frozenset(),
}
_TERMINAL_STATUSES = frozenset({"completed", "abandoned"})


class InvalidCampaignNameError(ValueError):
    """Raised when a campaign name contains characters other than letters, numbers, underscores, and hyphens."""


class InvalidCampaignTransitionError(ValueError):
    """Raised when a campaign status transition isn't permitted from the campaign's current status."""


class AnotherCampaignOpenError(ValueError):
    """Raised when opening a campaign while a different campaign is already open."""


class CampaignHasOpenEncountersError(ValueError):
    """Raised when pausing, completing, or abandoning a campaign that still has an open encounter."""


class CampaignNotTerminalError(ValueError):
    """Raised when archiving a campaign whose status isn't 'completed' or 'abandoned'."""


class CampaignAlreadyArchivedError(ValueError):
    """Raised when archiving a campaign that is already archived."""


class CampaignHasUnfinishedEncountersError(ValueError):
    """Raised when archiving a campaign that has one or more encounters not yet 'completed' or
    'abandoned'."""


class NoActiveCampaignError(ValueError):
    """Raised when a campaign must be resolved from the active (open) campaign but none is open."""


class CampaignNotMutableError(ValueError):
    """Raised when an operation that mutates a campaign's encounters, or a campaign's own body,
    targets a campaign whose status is terminal (completed or abandoned)."""


class CampaignMessageRequiredError(ValueError):
    """Raised when a required postmortem message is missing or blank."""


class CampaignNotFoundError(FileNotFoundError):
    """Raised when a named campaign file does not exist."""


class CampaignAlreadyExistsError(FileExistsError):
    """Raised when a named campaign file already exists."""


@dataclass(frozen=True)
class Campaign:
    name: str
    status: str
    archived: bool
    body: str


def campaign_dir(root: Path) -> Path:
    return sourcebook_dir(root) / CAMPAIGN_DIR_NAME


def archive_campaign_dir(root: Path) -> Path:
    return sourcebook_dir(root) / ARCHIVE_DIR_NAME / CAMPAIGN_DIR_NAME


def validate_name(name: str) -> None:
    if not NAME_PATTERN.fullmatch(name) or name in RESERVED_NAMES:
        raise InvalidCampaignNameError(
            f"Campaign name {name!r} is invalid: only letters, numbers, underscores, hyphens, and periods are "
            "allowed (and the name cannot be '.' or '..')."
        )


def exists(root: Path, name: str) -> bool:
    validate_name(name)
    return (campaign_dir(root) / f"{name}.md").exists()


def list_campaigns(root: Path) -> list[str]:
    directory = campaign_dir(root)
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*.md"))


def list_archived_campaigns(root: Path) -> list[str]:
    """List archived campaign names, e.g. for the search index to include archived content
    alongside live content when rebuilding from disk."""
    directory = archive_campaign_dir(root)
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*.md"))


def list_campaigns_with_status(root: Path) -> list[tuple[str, str]]:
    directory = campaign_dir(root)
    if not directory.is_dir():
        return []
    result = []
    for path in sorted(directory.glob("*.md")):
        post = frontmatter.load(path)
        result.append((path.stem, post.get("status", DEFAULT_CAMPAIGN_STATUS)))
    return result


def template_body() -> str:
    return frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME)).content


def active_campaign(root: Path) -> str | None:
    """Return the name of the single open campaign, or None if none is open. Only one campaign may
    be open at a time, so the first match is the active campaign."""
    for name, status in list_campaigns_with_status(root):
        if status == "open":
            return name
    return None


def resolve_campaign(root: Path, campaign: str | None, *, require_mutable: bool) -> str:
    """Resolve the campaign an encounter command should act on.

    When `campaign` is None, fall back to the active (open) campaign, raising NoActiveCampaignError
    if none is open. When `campaign` is given, verify it exists and - if `require_mutable` - that its
    status is not terminal (completed/abandoned)."""
    if campaign is None:
        active = active_campaign(root)
        if active is None:
            raise NoActiveCampaignError(
                "No campaign is currently open. Open a campaign first, or pass --campaign to target a specific one."
            )
        return active
    path = _existing_campaign_path(root, campaign)
    if require_mutable:
        status = frontmatter.load(path).get("status", DEFAULT_CAMPAIGN_STATUS)
        if status in _TERMINAL_STATUSES:
            raise CampaignNotMutableError(
                f"Campaign {campaign!r} is {status!r}; its encounters can no longer be created or modified. "
                "Only campaigns that are not completed or abandoned may be changed."
            )
    return campaign


def read_campaign(root: Path, name: str) -> Campaign:
    post = frontmatter.load(_existing_campaign_path(root, name))
    return _to_campaign(post, name)


def read_metadata(root: Path, name: str) -> tuple[dict[str, Any], str]:
    post = frontmatter.load(_existing_campaign_path(root, name))
    return dict(post.metadata), post.content


def campaign_path(root: Path, name: str) -> Path:
    """Return the on-disk path for a campaign, e.g. for use in a truncation fallback notice.
    Resolves the live location first, then the archive location, so this stays correct for an
    archived campaign too."""
    return _existing_campaign_path(root, name)


def create_campaign(root: Path, name: str, body: str) -> Path:
    path = _campaign_path(root, name)
    if path.exists():
        raise CampaignAlreadyExistsError(f"Campaign {name!r} already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME))
    post["name"] = name
    post.content = body
    frontmatter_utils.stamp_created(post, root)
    write_post(root, path, post)
    return path


def update_campaign(root: Path, name: str, body: str) -> Path:
    path = _existing_campaign_path(root, name)
    post = frontmatter.load(path)
    status = post.get("status", DEFAULT_CAMPAIGN_STATUS)
    if status in _TERMINAL_STATUSES:
        raise CampaignNotMutableError(
            f"Campaign {name!r} is {status!r}; its body is locked once a campaign is completed or abandoned. "
            "The postmortem recorded at that transition is the closing record and cannot be rewritten."
        )
    post.content = body
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return path


def delete_campaign(root: Path, name: str) -> Path:
    path = _existing_campaign_path(root, name)
    return frontmatter_utils.delete_post(root, path)


def open_campaign(root: Path, name: str) -> Campaign:
    """Move a campaign from 'draft' or 'paused' to 'open'. Fails if a different campaign is
    already open - only one campaign may be open at a time."""
    path = _existing_campaign_path(root, name)
    post = frontmatter.load(path)
    _check_transition(post, name, to_status="open")
    other = _other_open_campaign(root, exclude=name)
    if other is not None:
        raise AnotherCampaignOpenError(
            f"Cannot open campaign {name!r}: campaign {other!r} is already open. Only one campaign may be "
            f"open at a time; pause or complete {other!r} first."
        )
    return _apply_status(post, path, name, "open", root)


def pause_campaign(root: Path, name: str) -> Campaign:
    """Move a campaign from 'open' to 'paused'. Fails if the campaign has an open encounter."""
    return _guarded_transition(root, name, to_status="paused", action="pause", log_heading=None, message=None)


def complete_campaign(root: Path, name: str, message: str) -> Campaign:
    """Move a campaign from 'open' or 'paused' to 'completed'. Fails if the campaign has an open
    encounter. A postmortem message is required and is appended as a dated, attributed log entry
    on the campaign body."""
    return _guarded_transition(
        root, name, to_status="completed", action="complete", log_heading="Completed", message=message
    )


def abandon_campaign(root: Path, name: str, message: str) -> Campaign:
    """Move a campaign from 'draft', 'open', or 'paused' to 'abandoned'. Fails if the campaign has
    an open encounter. A postmortem message is required and is appended as a dated, attributed log
    entry on the campaign body."""
    return _guarded_transition(
        root, name, to_status="abandoned", action="abandon", log_heading="Abandoned", message=message
    )


def archive_campaign(root: Path, name: str) -> tuple[Campaign, list[str]]:
    """Archive a campaign and every one of its encounters: move them from the live
    campaigns/encounters directories into .sourcebook/archive/, mirroring the live layout, and set
    archived: true on each. status is left untouched - archiving is not a status transition.

    Requires the campaign to already be 'completed' or 'abandoned', not already archived, and every
    one of its encounters to also be 'completed' or 'abandoned' - a strictly broader check than
    complete/abandon's existing open-encounter guard. Returns the updated Campaign and the names of
    every encounter archived alongside it."""
    from cac.core import encounter as encounter_core

    path = _existing_campaign_path(root, name)
    post = frontmatter.load(path)
    status = post.get("status", DEFAULT_CAMPAIGN_STATUS)
    if status not in _TERMINAL_STATUSES:
        raise CampaignNotTerminalError(
            f"Cannot archive campaign {name!r}: status is {status!r}. Only 'completed' or "
            "'abandoned' campaigns may be archived."
        )
    if post.get(ARCHIVED_KEY, False):
        raise CampaignAlreadyArchivedError(f"Campaign {name!r} is already archived.")
    unfinished = encounter_core.unfinished_encounter_names(root, name)
    if unfinished:
        details = ", ".join(f"{encounter_name} ({encounter_status})" for encounter_name, encounter_status in unfinished)
        raise CampaignHasUnfinishedEncountersError(
            f"Cannot archive campaign {name!r}: it has unfinished encounter(s) {details}. "
            "Complete or abandon them first."
        )

    archived_encounters = encounter_core.archive_encounters(root, name)

    frontmatter_utils.stamp_updated(post, root)
    post[ARCHIVED_KEY] = True
    new_path = archive_campaign_dir(root) / f"{name}.md"
    new_path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter_utils.write_post(root, new_path, post)
    path.unlink()

    return _to_campaign(post, name), archived_encounters


def _guarded_transition(
    root: Path, name: str, *, to_status: str, action: str, log_heading: str | None, message: str | None
) -> Campaign:
    path = _existing_campaign_path(root, name)
    post = frontmatter.load(path)
    _check_transition(post, name, to_status=to_status)
    open_encounters = _open_encounter_names(root, name)
    if open_encounters:
        raise CampaignHasOpenEncountersError(
            f"Cannot {action} campaign {name!r}: it has open encounter(s) {', '.join(open_encounters)}. "
            "Complete or abandon them first."
        )
    if to_status in _TERMINAL_STATUSES and not (message and message.strip()):
        raise CampaignMessageRequiredError(
            f"A --message is required to move campaign {name!r} to {to_status!r}; it is recorded as this "
            "campaign's postmortem."
        )
    return _apply_status(post, path, name, to_status, root, log_heading=log_heading, message=message)


def _check_transition(post: frontmatter.Post, name: str, *, to_status: str) -> None:
    current_status = post.get("status", DEFAULT_CAMPAIGN_STATUS)
    allowed = _CAMPAIGN_TRANSITIONS.get(current_status, frozenset())
    if to_status not in allowed:
        raise InvalidCampaignTransitionError(
            f"Cannot move campaign {name!r} from status {current_status!r} to {to_status!r}. "
            f"Allowed transitions from {current_status!r}: {', '.join(sorted(allowed)) or 'none (terminal status)'}."
        )


def _apply_status(
    post: frontmatter.Post,
    path: Path,
    name: str,
    to_status: str,
    root: Path,
    *,
    log_heading: str | None = None,
    message: str | None = None,
) -> Campaign:
    user = frontmatter_utils.stamp_updated(post, root)
    if message:
        frontmatter_utils.append_log_entry(post, section=_LOG_SECTION, heading=log_heading, message=message, user=user)
    post["status"] = to_status
    write_post(root, path, post)
    return _to_campaign(post, name)


def _other_open_campaign(root: Path, exclude: str) -> str | None:
    active = active_campaign(root)
    return active if active != exclude else None


def _open_encounter_names(root: Path, name: str) -> list[str]:
    directory = sourcebook_dir(root) / ENCOUNTER_DIR_NAME / name
    if not directory.is_dir():
        return []
    names = []
    for path in sorted(directory.glob("*.md")):
        post = frontmatter.load(path)
        if post.get("status", DEFAULT_ENCOUNTER_STATUS) == "open":
            names.append(path.stem)
    return names


def _to_campaign(post: frontmatter.Post, name: str) -> Campaign:
    return Campaign(
        name=post.get("name", name),
        status=post.get("status", DEFAULT_CAMPAIGN_STATUS),
        archived=post.get(ARCHIVED_KEY, False),
        body=post.content,
    )


def _campaign_path(root: Path, name: str) -> Path:
    validate_name(name)
    return campaign_dir(root) / f"{name}.md"


def _existing_campaign_path(root: Path, name: str) -> Path:
    path = _campaign_path(root, name)
    if path.exists():
        return path
    archived_path = archive_campaign_dir(root) / f"{name}.md"
    if archived_path.exists():
        return archived_path
    raise CampaignNotFoundError(f"Campaign {name!r} does not exist.")
