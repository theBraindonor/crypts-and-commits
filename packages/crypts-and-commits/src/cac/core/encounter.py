from dataclasses import dataclass
from pathlib import Path

import frontmatter

from cac.core import campaign as campaign_core
from cac.core import region as region_core
from cac.core import templates
from cac.core.config import DEFAULT_ENCOUNTER_STATUS, ENCOUNTER_DIR_NAME, ENCOUNTER_STATUSES, NAME_PATTERN
from cac.core.frontmatter_utils import toggle_list_attribute, write_post
from cac.core.paths import sourcebook_dir

_TEMPLATE_PACKAGE = "sourcebook"
_TEMPLATE_FILENAME = "encounter.md"
REGIONS_KEY = "regions"


class InvalidEncounterNameError(ValueError):
    """Raised when an encounter name contains characters other than letters, numbers, underscores, and hyphens."""


class InvalidEncounterStatusError(ValueError):
    """Raised when an encounter status is not one of the allowed values."""


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


def encounter_dir(root: Path, campaign: str) -> Path:
    campaign_core.validate_name(campaign)
    return sourcebook_dir(root) / ENCOUNTER_DIR_NAME / campaign


def validate_name(name: str) -> None:
    if not NAME_PATTERN.fullmatch(name):
        raise InvalidEncounterNameError(
            f"Encounter name {name!r} is invalid: only letters, numbers, underscores, and hyphens are allowed."
        )


def validate_status(status: str) -> None:
    if status not in ENCOUNTER_STATUSES:
        allowed = ", ".join(ENCOUNTER_STATUSES)
        raise InvalidEncounterStatusError(f"Encounter status {status!r} is invalid: must be one of {allowed}.")


def exists(root: Path, campaign: str, name: str) -> bool:
    validate_name(name)
    return (encounter_dir(root, campaign) / f"{name}.md").exists()


def list_encounters(root: Path, campaign: str) -> list[str]:
    directory = encounter_dir(root, campaign)
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*.md"))


def template_body() -> str:
    return frontmatter.loads(templates.load(_TEMPLATE_PACKAGE, _TEMPLATE_FILENAME)).content


def read_encounter(root: Path, campaign: str, name: str) -> Encounter:
    post = frontmatter.load(_existing_encounter_path(root, campaign, name))
    return _to_encounter(post, campaign, name)


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
    write_post(path, post)
    return path


def update_encounter(root: Path, campaign: str, name: str, body: str) -> Path:
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    post.content = body
    write_post(path, post)
    return path


def delete_encounter(root: Path, campaign: str, name: str) -> Path:
    path = _existing_encounter_path(root, campaign, name)
    path.unlink()
    return path


def set_status(root: Path, campaign: str, name: str, status: str) -> Encounter:
    validate_status(status)
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    post["status"] = status
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
