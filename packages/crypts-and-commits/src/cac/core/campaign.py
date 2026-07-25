from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from cac.core import frontmatter_utils, git_utils, templates
from cac.core.config import (
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
CREATED_BY_KEY = "created_by"
CREATED_ON_KEY = "created_on"
UPDATED_BY_KEY = "updated_by"
UPDATED_ON_KEY = "updated_on"

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


class NoActiveCampaignError(ValueError):
    """Raised when a campaign must be resolved from the active (open) campaign but none is open."""


class CampaignNotMutableError(ValueError):
    """Raised when an operation that mutates a campaign's encounters targets a campaign whose status
    is terminal (completed or abandoned)."""


class CampaignNotFoundError(FileNotFoundError):
    """Raised when a named campaign file does not exist."""


class CampaignAlreadyExistsError(FileExistsError):
    """Raised when a named campaign file already exists."""


@dataclass(frozen=True)
class Campaign:
    name: str
    status: str
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


def campaign_dir(root: Path) -> Path:
    return sourcebook_dir(root) / CAMPAIGN_DIR_NAME


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
    """Return the on-disk path for a campaign, e.g. for use in a truncation fallback notice."""
    return _campaign_path(root, name)


def create_campaign(root: Path, name: str, body: str) -> Path:
    path = _campaign_path(root, name)
    if path.exists():
        raise CampaignAlreadyExistsError(f"Campaign {name!r} already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME))
    post["name"] = name
    post.content = body
    _stamp_created(post, root)
    write_post(path, post)
    return path


def update_campaign(root: Path, name: str, body: str) -> Path:
    path = _existing_campaign_path(root, name)
    post = frontmatter.load(path)
    post.content = body
    _stamp_updated(post, root)
    write_post(path, post)
    return path


def delete_campaign(root: Path, name: str) -> Path:
    path = _existing_campaign_path(root, name)
    path.unlink()
    return path


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
    return _guarded_transition(root, name, to_status="paused", action="pause")


def complete_campaign(root: Path, name: str) -> Campaign:
    """Move a campaign from 'open' or 'paused' to 'completed'. Fails if the campaign has an open
    encounter."""
    return _guarded_transition(root, name, to_status="completed", action="complete")


def abandon_campaign(root: Path, name: str) -> Campaign:
    """Move a campaign from 'draft', 'open', or 'paused' to 'abandoned'. Fails if the campaign has
    an open encounter."""
    return _guarded_transition(root, name, to_status="abandoned", action="abandon")


def _guarded_transition(root: Path, name: str, *, to_status: str, action: str) -> Campaign:
    path = _existing_campaign_path(root, name)
    post = frontmatter.load(path)
    _check_transition(post, name, to_status=to_status)
    open_encounters = _open_encounter_names(root, name)
    if open_encounters:
        raise CampaignHasOpenEncountersError(
            f"Cannot {action} campaign {name!r}: it has open encounter(s) {', '.join(open_encounters)}. "
            "Complete or abandon them first."
        )
    return _apply_status(post, path, name, to_status, root)


def _check_transition(post: frontmatter.Post, name: str, *, to_status: str) -> None:
    current_status = post.get("status", DEFAULT_CAMPAIGN_STATUS)
    allowed = _CAMPAIGN_TRANSITIONS.get(current_status, frozenset())
    if to_status not in allowed:
        raise InvalidCampaignTransitionError(
            f"Cannot move campaign {name!r} from status {current_status!r} to {to_status!r}. "
            f"Allowed transitions from {current_status!r}: {', '.join(sorted(allowed)) or 'none (terminal status)'}."
        )


def _apply_status(post: frontmatter.Post, path: Path, name: str, to_status: str, root: Path) -> Campaign:
    _stamp_updated(post, root)
    post["status"] = to_status
    write_post(path, post)
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
        body=post.content,
    )


def _campaign_path(root: Path, name: str) -> Path:
    validate_name(name)
    return campaign_dir(root) / f"{name}.md"


def _existing_campaign_path(root: Path, name: str) -> Path:
    path = _campaign_path(root, name)
    if not path.exists():
        raise CampaignNotFoundError(f"Campaign {name!r} does not exist.")
    return path
