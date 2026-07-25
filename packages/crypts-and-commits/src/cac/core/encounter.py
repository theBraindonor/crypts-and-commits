from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from cac.core import campaign as campaign_core
from cac.core import frontmatter_utils
from cac.core import git_utils
from cac.core import region as region_core
from cac.core import templates
from cac.core.config import (
    DEFAULT_ENCOUNTER_STATUS,
    ENCOUNTER_DIR_NAME,
    NAME_PATTERN,
    RESERVED_NAMES,
)
from cac.core.frontmatter_utils import toggle_list_attribute, write_post
from cac.core.paths import sourcebook_dir

_TEMPLATE_PACKAGE = "sourcebook"
_TEMPLATE_FILENAME = "encounter.md"
REGIONS_KEY = "regions"
_LOG_SECTION = "Log"
CREATED_BY_KEY = "created_by"
CREATED_ON_KEY = "created_on"
UPDATED_BY_KEY = "updated_by"
UPDATED_ON_KEY = "updated_on"

_ENCOUNTER_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"reviewed", "abandoned"}),
    "reviewed": frozenset({"open", "abandoned"}),
    "open": frozenset({"completed", "abandoned"}),
    "completed": frozenset(),
    "abandoned": frozenset(),
}
_RECORD_MESSAGE_STATUSES = frozenset({"reviewed", "open"})


class InvalidEncounterNameError(ValueError):
    """Raised when an encounter name contains characters other than letters, numbers, underscores, and hyphens."""


class InvalidEncounterTransitionError(ValueError):
    """Raised when an encounter status transition, or a status-gated operation, isn't permitted from the
    encounter's current status."""


class EncounterNotDraftError(InvalidEncounterTransitionError):
    """Raised when attempting to replace an encounter's body while its status isn't 'draft'."""


class EncounterMessageRequiredError(ValueError):
    """Raised when a required message is missing or blank."""


class EncounterNotFoundError(FileNotFoundError):
    """Raised when a named encounter file does not exist."""


class EncounterAlreadyExistsError(FileExistsError):
    """Raised when a named encounter file already exists."""


@dataclass(frozen=True)
class Encounter:
    name: str
    campaign: str
    status: str
    regions: list[str]
    body: str


def _stamp_created(post: frontmatter.Post, root: Path) -> str:
    user = git_utils.current_git_user(root)
    ts = frontmatter_utils.format_timestamp(frontmatter_utils.utcnow())
    post[CREATED_BY_KEY] = user
    post[CREATED_ON_KEY] = ts
    post[UPDATED_BY_KEY] = user
    post[UPDATED_ON_KEY] = ts
    return user


def _stamp_updated(post: frontmatter.Post, root: Path) -> str:
    user = git_utils.current_git_user(root)
    post[UPDATED_BY_KEY] = user
    post[UPDATED_ON_KEY] = frontmatter_utils.format_timestamp(frontmatter_utils.utcnow())
    return user


def encounter_dir(root: Path, campaign: str) -> Path:
    campaign_core.validate_name(campaign)
    return sourcebook_dir(root) / ENCOUNTER_DIR_NAME / campaign


def validate_name(name: str) -> None:
    if not NAME_PATTERN.fullmatch(name) or name in RESERVED_NAMES:
        raise InvalidEncounterNameError(
            f"Encounter name {name!r} is invalid: only letters, numbers, underscores, hyphens, and periods are "
            "allowed (and the name cannot be '.' or '..')."
        )


def exists(root: Path, campaign: str, name: str) -> bool:
    validate_name(name)
    return (encounter_dir(root, campaign) / f"{name}.md").exists()


def list_encounters(root: Path, campaign: str) -> list[str]:
    """List encounter names in a campaign, ascending by their `updated_on` timestamp (oldest first).
    Encounters missing `updated_on` are treated as EPOCH and sort first; the stored timestamp format
    (`%Y-%m-%dT%H:%M:%SZ`) is fixed-width, so a plain text comparison orders them chronologically."""
    directory = encounter_dir(root, campaign)
    if not directory.is_dir():
        return []
    paths = directory.glob("*.md")
    return [path.stem for path in sorted(paths, key=lambda p: frontmatter.load(p).get(UPDATED_ON_KEY, ""))]


def template_body() -> str:
    return frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME)).content


def read_encounter(root: Path, campaign: str, name: str) -> Encounter:
    post = frontmatter.load(_existing_encounter_path(root, campaign, name))
    return _to_encounter(post, campaign, name)


def read_metadata(root: Path, campaign: str, name: str) -> tuple[dict[str, Any], str]:
    post = frontmatter.load(_existing_encounter_path(root, campaign, name))
    return dict(post.metadata), post.content


def encounter_path(root: Path, campaign: str, name: str) -> Path:
    """Return the on-disk path for an encounter, e.g. for use in a truncation fallback notice."""
    return _encounter_path(root, campaign, name)


def create_encounter(root: Path, campaign: str, name: str, body: str) -> Path:
    if not campaign_core.exists(root, campaign):
        raise campaign_core.CampaignNotFoundError(f"Campaign {campaign!r} does not exist.")
    path = _encounter_path(root, campaign, name)
    if path.exists():
        raise EncounterAlreadyExistsError(f"Encounter {name!r} already exists in campaign {campaign!r}.")
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME))
    post["name"] = name
    post["campaign"] = campaign
    post.content = body
    _stamp_created(post, root)
    write_post(path, post)
    return path


def update_encounter(root: Path, campaign: str, name: str, body: str) -> Path:
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    current_status = post.get("status", DEFAULT_ENCOUNTER_STATUS)
    if current_status != "draft":
        raise EncounterNotDraftError(
            f"Encounter {name!r} is in status {current_status!r}; its content can only be replaced while in "
            "'draft' status. Use 'cac encounter record-message' to append additional context instead."
        )
    post.content = body
    _stamp_updated(post, root)
    write_post(path, post)
    return path


def delete_encounter(root: Path, campaign: str, name: str) -> Path:
    path = _existing_encounter_path(root, campaign, name)
    path.unlink()
    return path


def review_encounter(root: Path, campaign: str, name: str, message: str) -> Encounter:
    """Move an encounter from 'draft' to 'reviewed'. Message is required and permanently locks
    the Requirements/Rationale/Plan/Verification sections against further replacement."""
    return _transition(
        root, campaign, name, to_status="reviewed", log_heading="Review", message=message, message_required=True
    )


def abandon_encounter(root: Path, campaign: str, name: str, message: str) -> Encounter:
    """Move an encounter from 'draft', 'reviewed', or 'open' to 'abandoned'. Message is required.
    Not reachable from 'completed' or 'abandoned'."""
    return _transition(
        root, campaign, name, to_status="abandoned", log_heading="Abandoned", message=message, message_required=True
    )


def open_encounter(root: Path, campaign: str, name: str, message: str | None = None) -> Encounter:
    """Move an encounter from 'reviewed' to 'open'. Message is optional."""
    return _transition(
        root, campaign, name, to_status="open", log_heading="Opened", message=message, message_required=False
    )


def complete_encounter(root: Path, campaign: str, name: str, message: str | None = None) -> Encounter:
    """Move an encounter from 'open' to 'completed'. Message is optional."""
    return _transition(
        root, campaign, name, to_status="completed", log_heading="Completed", message=message, message_required=False
    )


def record_message(root: Path, campaign: str, name: str, message: str) -> Encounter:
    """Append a message to an encounter without changing its status. Valid only while status is
    'reviewed' or 'open'."""
    if not message or not message.strip():
        raise EncounterMessageRequiredError(f"A message is required to record a message on encounter {name!r}.")
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    current_status = post.get("status", DEFAULT_ENCOUNTER_STATUS)
    if current_status not in _RECORD_MESSAGE_STATUSES:
        allowed = ", ".join(sorted(_RECORD_MESSAGE_STATUSES))
        raise InvalidEncounterTransitionError(
            f"Cannot record a message on encounter {name!r}: status is {current_status!r}, but recording a "
            f"message requires status to be one of: {allowed}."
        )
    user = _stamp_updated(post, root)
    frontmatter_utils.append_log_entry(post, section=_LOG_SECTION, heading="Message", message=message, user=user)
    write_post(path, post)
    return _to_encounter(post, campaign, name)


def _transition(
    root: Path,
    campaign: str,
    name: str,
    *,
    to_status: str,
    log_heading: str,
    message: str | None,
    message_required: bool,
) -> Encounter:
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    current_status = post.get("status", DEFAULT_ENCOUNTER_STATUS)
    allowed = _ENCOUNTER_TRANSITIONS.get(current_status, frozenset())
    if to_status not in allowed:
        raise InvalidEncounterTransitionError(
            f"Cannot move encounter {name!r} from status {current_status!r} to {to_status!r}. "
            f"Allowed transitions from {current_status!r}: "
            f"{', '.join(sorted(allowed)) or 'none (terminal status)'}."
        )
    if message_required and not (message and message.strip()):
        raise EncounterMessageRequiredError(f"A --message is required to move encounter {name!r} to {to_status!r}.")
    user = _stamp_updated(post, root)
    if message:
        frontmatter_utils.append_log_entry(post, section=_LOG_SECTION, heading=log_heading, message=message, user=user)
    post["status"] = to_status
    write_post(path, post)
    return _to_encounter(post, campaign, name)


def assign_region(root: Path, campaign: str, name: str, region: str) -> Encounter:
    """Assign an encounter to a region. The link is recorded only on the encounter."""
    if not region_core.exists(root, region):
        raise region_core.RegionNotFoundError(f"Region {region!r} does not exist.")
    return _update_regions(root, campaign, name, add=region)


def unassign_region(root: Path, campaign: str, name: str, region: str) -> Encounter:
    return _update_regions(root, campaign, name, remove=region)


def _update_regions(
    root: Path, campaign: str, name: str, *, add: str | None = None, remove: str | None = None
) -> Encounter:
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    toggle_list_attribute(post, REGIONS_KEY, add=add, remove=remove)
    _stamp_updated(post, root)
    write_post(path, post)
    return _to_encounter(post, campaign, name)


def _to_encounter(post: frontmatter.Post, campaign: str, name: str) -> Encounter:
    return Encounter(
        name=post.get("name", name),
        campaign=post.get("campaign", campaign),
        status=post.get("status", DEFAULT_ENCOUNTER_STATUS),
        regions=post.get("regions", []),
        body=post.content,
    )


def _encounter_path(root: Path, campaign: str, name: str) -> Path:
    validate_name(name)
    return encounter_dir(root, campaign) / f"{name}.md"


def _existing_encounter_path(root: Path, campaign: str, name: str) -> Path:
    path = _encounter_path(root, campaign, name)
    if not path.exists():
        raise EncounterNotFoundError(f"Encounter {name!r} does not exist in campaign {campaign!r}.")
    return path
