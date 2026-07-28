import heapq
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter

from cac.core import campaign as campaign_core
from cac.core import frontmatter_utils, templates
from cac.core import region as region_core
from cac.core.config import (
    CREATED_ON_KEY,
    DEFAULT_ENCOUNTER_STATUS,
    ENCOUNTER_DIR_NAME,
    NAME_PATTERN,
    RESERVED_NAMES,
    UPDATED_ON_KEY,
)
from cac.core.frontmatter_utils import toggle_list_attribute, write_post
from cac.core.paths import sourcebook_dir

_TEMPLATE_PACKAGE = "sourcebook"
_TEMPLATE_FILENAME = "encounter.md"
REGIONS_KEY = "regions"
DEPENDS_ON_KEY = "depends_on"
_LOG_SECTION = "Log"

_ENCOUNTER_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"reviewed", "abandoned"}),
    "reviewed": frozenset({"open", "abandoned"}),
    "open": frozenset({"completed", "abandoned"}),
    "completed": frozenset(),
    "abandoned": frozenset(),
}
_RECORD_MESSAGE_STATUSES = frozenset({"reviewed", "open"})
_DEPENDENCY_MUTATION_STATUSES = frozenset({"draft"})
_REGION_MUTATION_STATUSES = frozenset({"draft"})


class InvalidEncounterNameError(ValueError):
    """Raised when an encounter name contains characters other than letters, numbers, underscores, and hyphens."""


class InvalidEncounterTransitionError(ValueError):
    """Raised when an encounter status transition, or a status-gated operation, isn't permitted from the
    encounter's current status."""


class EncounterNotDraftError(InvalidEncounterTransitionError):
    """Raised when attempting to replace an encounter's body while its status isn't 'draft'."""


class EncounterMessageRequiredError(ValueError):
    """Raised when a required message is missing or blank."""


class EncounterRegionMutationError(ValueError):
    """Raised when a region is assigned or unassigned after an encounter has left 'draft'/'reviewed'."""


class EncounterRegionRequiredError(ValueError):
    """Raised when reviewing a draft encounter that has no regions assigned."""


class EncounterNotFoundError(FileNotFoundError):
    """Raised when a named encounter file does not exist."""


class EncounterAlreadyExistsError(FileExistsError):
    """Raised when a named encounter file already exists."""


class EncounterDependencyError(ValueError):
    """Base class for encounter dependency failures."""


class EncounterDependencyMutationError(EncounterDependencyError):
    """Raised when dependencies are changed after an encounter has opened."""


class EncounterDependencyNotFoundError(EncounterDependencyError):
    """Raised when a dependency does not exist in the encounter's campaign."""


class EncounterSelfDependencyError(EncounterDependencyError):
    """Raised when an encounter is assigned as its own dependency."""


class EncounterAbandonedDependencyError(EncounterDependencyError):
    """Raised when an abandoned encounter is assigned as a dependency."""


class EncounterDependencyCycleError(EncounterDependencyError):
    """Raised when an encounter dependency graph contains a cycle."""


class EncounterDependenciesIncompleteError(EncounterDependencyError):
    """Raised when an encounter is opened before all of its dependencies are completed."""


class EncounterHasDependentsError(EncounterDependencyError):
    """Raised when deleting an encounter that other encounters depend on."""


class InvalidEncounterDependencyGraphError(EncounterDependencyError):
    """Raised when stored dependency metadata is malformed or references a missing encounter."""


@dataclass(frozen=True)
class Encounter:
    name: str
    campaign: str
    status: str
    regions: list[str]
    depends_on: list[str]
    body: str


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
    frontmatter_utils.stamp_created(post, root)
    write_post(root, path, post)
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
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return path


def delete_encounter(root: Path, campaign: str, name: str) -> Path:
    path = _existing_encounter_path(root, campaign, name)
    dependents = sorted(
        other_name
        for other_name, post in _load_campaign_posts(root, campaign).items()
        if other_name != name and name in _dependencies(post, other_name)
    )
    if dependents:
        raise EncounterHasDependentsError(
            f"Cannot delete encounter {name!r}: it is required by: {', '.join(dependents)}."
        )
    return frontmatter_utils.delete_post(root, path)


def review_encounter(root: Path, campaign: str, name: str, message: str) -> Encounter:
    """Move an encounter from 'draft' to 'reviewed'. Requires at least one region to already be
    assigned. Message is required and permanently locks the Requirements/Rationale/Plan/Verification
    sections against further replacement."""
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    if post.get("status", DEFAULT_ENCOUNTER_STATUS) == "draft" and not post.get(REGIONS_KEY, []):
        raise EncounterRegionRequiredError(
            f"Cannot review encounter {name!r}: at least one region must be assigned first "
            "(use 'assign_region' / 'cac encounter assign-region')."
        )
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
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    if post.get("status", DEFAULT_ENCOUNTER_STATUS) == "reviewed":
        posts = _load_campaign_posts(root, campaign)
        blockers: list[tuple[str, str]] = []
        for dependency in _dependencies(post, name):
            dependency_post = posts.get(dependency)
            dependency_status = (
                dependency_post.get("status", DEFAULT_ENCOUNTER_STATUS) if dependency_post is not None else "missing"
            )
            if dependency_status != "completed":
                blockers.append((dependency, dependency_status))
        if blockers:
            details = ", ".join(f"{dependency} ({status})" for dependency, status in blockers)
            raise EncounterDependenciesIncompleteError(
                f"Cannot open encounter {name!r}: incomplete dependencies: {details}."
            )
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
    user = frontmatter_utils.stamp_updated(post, root)
    frontmatter_utils.append_log_entry(post, section=_LOG_SECTION, heading="Message", message=message, user=user)
    write_post(root, path, post)
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
    user = frontmatter_utils.stamp_updated(post, root)
    if message:
        frontmatter_utils.append_log_entry(post, section=_LOG_SECTION, heading=log_heading, message=message, user=user)
    post["status"] = to_status
    write_post(root, path, post)
    return _to_encounter(post, campaign, name)


def assign_region(root: Path, campaign: str, name: str, region: str) -> Encounter:
    """Assign an encounter to a region. The link is recorded only on the encounter."""
    if not region_core.exists(root, region):
        raise region_core.RegionNotFoundError(f"Region {region!r} does not exist.")
    return _update_regions(root, campaign, name, add=region)


def unassign_region(root: Path, campaign: str, name: str, region: str) -> Encounter:
    return _update_regions(root, campaign, name, remove=region)


def assign_dependency(root: Path, campaign: str, name: str, dependency: str) -> Encounter:
    """Add a direct prerequisite to an encounter while it is draft."""
    validate_name(dependency)
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    _require_dependency_mutable(post, name)
    current = _dependencies(post, name)
    if dependency in current:
        frontmatter_utils.stamp_updated(post, root)
        write_post(root, path, post)
        return _to_encounter(post, campaign, name)
    if dependency == name:
        raise EncounterSelfDependencyError(f"Encounter {name!r} cannot depend on itself.")
    dependency_path = _encounter_path(root, campaign, dependency)
    if not dependency_path.exists():
        raise EncounterDependencyNotFoundError(f"Dependency {dependency!r} does not exist in campaign {campaign!r}.")
    dependency_post = frontmatter.load(dependency_path)
    if dependency_post.get("status", DEFAULT_ENCOUNTER_STATUS) == "abandoned":
        raise EncounterAbandonedDependencyError(
            f"Encounter {name!r} cannot depend on abandoned encounter {dependency!r}."
        )

    posts = _load_campaign_posts(root, campaign)
    post[DEPENDS_ON_KEY] = [*current, dependency]
    posts[name] = post
    _validate_and_order(posts)
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return _to_encounter(post, campaign, name)


def unassign_dependency(root: Path, campaign: str, name: str, dependency: str) -> Encounter:
    """Remove a direct prerequisite while the dependent encounter is draft."""
    validate_name(dependency)
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    _require_dependency_mutable(post, name)
    current = _dependencies(post, name)
    post[DEPENDS_ON_KEY] = [item for item in current if item != dependency]
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return _to_encounter(post, campaign, name)


def order_encounters(root: Path, campaign: str) -> list[Encounter]:
    """Return all campaign encounters in deterministic topological order."""
    posts = _load_campaign_posts(root, campaign)
    names = _validate_and_order(posts)
    return [_to_encounter(posts[name], campaign, name) for name in names]


def _update_regions(
    root: Path, campaign: str, name: str, *, add: str | None = None, remove: str | None = None
) -> Encounter:
    path = _existing_encounter_path(root, campaign, name)
    post = frontmatter.load(path)
    _require_region_mutable(post, name)
    toggle_list_attribute(post, REGIONS_KEY, add=add, remove=remove)
    frontmatter_utils.stamp_updated(post, root)
    write_post(root, path, post)
    return _to_encounter(post, campaign, name)


def _to_encounter(post: frontmatter.Post, campaign: str, name: str) -> Encounter:
    return Encounter(
        name=post.get("name", name),
        campaign=post.get("campaign", campaign),
        status=post.get("status", DEFAULT_ENCOUNTER_STATUS),
        regions=post.get("regions", []),
        depends_on=post.get(DEPENDS_ON_KEY, []),
        body=post.content,
    )


def _require_dependency_mutable(post: frontmatter.Post, name: str) -> None:
    status = post.get("status", DEFAULT_ENCOUNTER_STATUS)
    if status not in _DEPENDENCY_MUTATION_STATUSES:
        allowed = ", ".join(sorted(_DEPENDENCY_MUTATION_STATUSES))
        raise EncounterDependencyMutationError(
            f"Cannot change dependencies for encounter {name!r}: status is {status!r}, but dependency changes "
            f"require status to be one of: {allowed}."
        )


def _require_region_mutable(post: frontmatter.Post, name: str) -> None:
    status = post.get("status", DEFAULT_ENCOUNTER_STATUS)
    if status not in _REGION_MUTATION_STATUSES:
        allowed = ", ".join(sorted(_REGION_MUTATION_STATUSES))
        raise EncounterRegionMutationError(
            f"Cannot change regions for encounter {name!r}: status is {status!r}, but region changes "
            f"require status to be one of: {allowed}."
        )


def _dependencies(post: frontmatter.Post, name: str) -> list[str]:
    value = post.get(DEPENDS_ON_KEY, [])
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise InvalidEncounterDependencyGraphError(
            f"Encounter {name!r} has invalid {DEPENDS_ON_KEY!r} metadata; expected a list of encounter names."
        )
    return value


def _load_campaign_posts(root: Path, campaign: str) -> dict[str, frontmatter.Post]:
    directory = encounter_dir(root, campaign)
    if not directory.is_dir():
        return {}
    return {path.stem: frontmatter.load(path) for path in directory.glob("*.md")}


def _validate_and_order(posts: dict[str, frontmatter.Post]) -> list[str]:
    dependencies: dict[str, list[str]] = {}
    missing: list[tuple[str, str]] = []
    for name, post in posts.items():
        dependencies[name] = _dependencies(post, name)
        missing.extend((name, dependency) for dependency in dependencies[name] if dependency not in posts)
    if missing:
        details = ", ".join(f"{name} -> {dependency}" for name, dependency in sorted(missing))
        raise InvalidEncounterDependencyGraphError(f"Encounter dependency graph has missing references: {details}.")

    indegree = {name: len(set(items)) for name, items in dependencies.items()}
    dependents: dict[str, set[str]] = {name: set() for name in posts}
    for name, items in dependencies.items():
        for dependency in set(items):
            dependents[dependency].add(name)

    def sort_key(name: str) -> tuple[str, str]:
        return str(posts[name].get(CREATED_ON_KEY, "")), name

    ready = [(sort_key(name), name) for name, degree in indegree.items() if degree == 0]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        _, name = heapq.heappop(ready)
        ordered.append(name)
        for dependent in dependents[name]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, (sort_key(dependent), dependent))

    if len(ordered) != len(posts):
        cycle = _find_dependency_cycle(dependencies)
        raise EncounterDependencyCycleError(f"Encounter dependency cycle detected: {' -> '.join(cycle)}.")
    return ordered


def _find_dependency_cycle(dependencies: dict[str, list[str]]) -> list[str]:
    visited: set[str] = set()
    active: list[str] = []
    active_set: set[str] = set()

    def visit(name: str) -> list[str] | None:
        if name in active_set:
            start = active.index(name)
            return [*active[start:], name]
        if name in visited:
            return None
        active.append(name)
        active_set.add(name)
        for dependency in dependencies[name]:
            cycle = visit(dependency)
            if cycle is not None:
                return cycle
        active.pop()
        active_set.remove(name)
        visited.add(name)
        return None

    for name in sorted(dependencies):
        cycle = visit(name)
        if cycle is not None:
            return cycle
    return []


def _encounter_path(root: Path, campaign: str, name: str) -> Path:
    validate_name(name)
    return encounter_dir(root, campaign) / f"{name}.md"


def _existing_encounter_path(root: Path, campaign: str, name: str) -> Path:
    path = _encounter_path(root, campaign, name)
    if not path.exists():
        raise EncounterNotFoundError(f"Encounter {name!r} does not exist in campaign {campaign!r}.")
    return path
