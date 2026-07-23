from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from cac.core import templates
from cac.core.config import CAMPAIGN_DIR_NAME, CAMPAIGN_STATUSES, DEFAULT_CAMPAIGN_STATUS, NAME_PATTERN
from cac.core.frontmatter_utils import write_post
from cac.core.paths import sourcebook_dir

_TEMPLATE_PACKAGE = "sourcebook"
_TEMPLATE_FILENAME = "campaign.md"


class InvalidCampaignNameError(ValueError):
    """Raised when a campaign name contains characters other than letters, numbers, underscores, and hyphens."""


class InvalidCampaignStatusError(ValueError):
    """Raised when a campaign status is not one of the allowed values."""


class CampaignNotFoundError(FileNotFoundError):
    """Raised when a named campaign file does not exist."""


class CampaignAlreadyExistsError(FileExistsError):
    """Raised when a named campaign file already exists."""


@dataclass(frozen=True)
class Campaign:
    name: str
    status: str
    body: str


def campaign_dir(root: Path) -> Path:
    return sourcebook_dir(root) / CAMPAIGN_DIR_NAME


def validate_name(name: str) -> None:
    if not NAME_PATTERN.fullmatch(name):
        raise InvalidCampaignNameError(
            f"Campaign name {name!r} is invalid: only letters, numbers, underscores, and hyphens are allowed."
        )


def validate_status(status: str) -> None:
    if status not in CAMPAIGN_STATUSES:
        allowed = ", ".join(CAMPAIGN_STATUSES)
        raise InvalidCampaignStatusError(f"Campaign status {status!r} is invalid: must be one of {allowed}.")


def exists(root: Path, name: str) -> bool:
    validate_name(name)
    return (campaign_dir(root) / f"{name}.md").exists()


def list_campaigns(root: Path) -> list[str]:
    directory = campaign_dir(root)
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*.md"))


def template_body() -> str:
    return frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME)).content


def read_campaign(root: Path, name: str) -> Campaign:
    post = frontmatter.load(_existing_campaign_path(root, name))
    return _to_campaign(post, name)


def read_metadata(root: Path, name: str) -> tuple[dict[str, Any], str]:
    post = frontmatter.load(_existing_campaign_path(root, name))
    return dict(post.metadata), post.content


def create_campaign(root: Path, name: str, body: str) -> Path:
    path = _campaign_path(root, name)
    if path.exists():
        raise CampaignAlreadyExistsError(f"Campaign {name!r} already exists.")
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME))
    post["name"] = name
    post.content = body
    write_post(path, post)
    return path


def update_campaign(root: Path, name: str, body: str) -> Path:
    path = _existing_campaign_path(root, name)
    post = frontmatter.load(path)
    post.content = body
    write_post(path, post)
    return path


def delete_campaign(root: Path, name: str) -> Path:
    path = _existing_campaign_path(root, name)
    path.unlink()
    return path


def set_status(root: Path, name: str, status: str) -> Campaign:
    validate_status(status)
    path = _existing_campaign_path(root, name)
    post = frontmatter.load(path)
    post["status"] = status
    write_post(path, post)
    return _to_campaign(post, name)


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
