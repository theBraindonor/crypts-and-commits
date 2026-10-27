from typing import Any

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail, reference_inputs, resolve_body_input
from cac.core import budget as budget_core
from cac.core import campaign as campaign_core
from cac.core import encounter as encounter_core
from cac.core import references
from cac.core import region as region_core
from cac.core.git_utils import GitIdentityError
from cac.core.paths import resolve_project_root

app = typer.Typer(
    help=(
        "Manage encounter entries - a concrete unit of work within a campaign, representing "
        "a plan the AI agent is expected to execute. An encounter moves through a fixed "
        "lifecycle: 'draft' (being planned; the only status in which its content may be "
        "replaced with 'update') -> 'reviewed' (via 'review', after a lore check; requires at "
        "least one assigned region and locks the content) -> 'open' (via 'open'; work begins) -> "
        "'completed' (via 'complete', after verification passes). It may instead be marked "
        "'abandoned' (via 'abandon') from 'draft', 'reviewed', or 'open' - but not once "
        "'completed'. Once past 'draft', content can no longer be replaced, only appended to via "
        "the 'review'/'abandon'/'open'/'complete' messages or 'record-message'. Regions and "
        "dependencies may only be changed while an encounter is 'draft'; all dependencies must be "
        "completed before it can open. "
        "Every encounter also has a 'kind', fixed at creation via --kind: 'scripted' (default; a "
        "plan for future work, all four sections apply) or 'unscripted' (a record of work already "
        "done outside the plan-first flow; only Requirements/Rationale apply). "
        "The campaign defaults to the active (open) campaign; use --campaign to target another one."
    )
)
console = Console()

_CAMPAIGN_HELP = "Campaign to act on. Defaults to the active (open) campaign."


def _campaign_option() -> Any:
    return typer.Option(None, "--campaign", "-c", help=_CAMPAIGN_HELP)


def _resolve_campaign(campaign: str | None, *, require_mutable: bool) -> str:
    """Resolve the campaign to act on, failing with a clear message if none is active, the named
    campaign does not exist, or (when mutating) it is completed/abandoned."""
    try:
        return campaign_core.resolve_campaign(resolve_project_root(), campaign, require_mutable=require_mutable)
    except (
        campaign_core.NoActiveCampaignError,
        campaign_core.CampaignNotFoundError,
        campaign_core.CampaignNotMutableError,
    ) as exc:
        fail(console, str(exc))


@app.command("get")
@reference_inputs("encounter")
def get_encounter(
    name: str = typer.Argument(..., help="Encounter name to show."),
    campaign: str | None = _campaign_option(),
) -> None:
    """Show an encounter file's frontmatter and body."""
    campaign = _resolve_campaign(campaign, require_mutable=False)
    try:
        metadata, body = encounter_core.read_metadata(resolve_project_root(), campaign, name)
    except encounter_core.EncounterNotFoundError as exc:
        fail(console, str(exc))

    for key, value in metadata.items():
        console.print(f"{key}: {value}", markup=False)
    console.print()
    body = budget_core.truncate_body(
        body,
        encounter_core.encounter_path(resolve_project_root(), campaign, name),
        budget=references.body_allowance(resolve_project_root(), "encounter", name, campaign),
    )
    console.print(body, markup=False, soft_wrap=True)


@app.command("list")
@reference_inputs("encounter")
def list_encounters(
    campaign: str | None = _campaign_option(),
    cursor: str | None = typer.Option(None, "--cursor", help="Resume from a previous page's cursor."),
) -> None:
    """List the encounter files in a campaign, oldest-updated first, paged under the response
    budget."""
    campaign = _resolve_campaign(campaign, require_mutable=False)
    names = encounter_core.list_encounters(resolve_project_root(), campaign)
    if not names:
        console.print("No encounter files found.", markup=False)
        return

    try:
        page_data = references.identity_page(resolve_project_root(), "encounter", names, cursor, campaign=campaign)
        page = budget_core.Page(items=page_data["items"], next_cursor=page_data["next_cursor"])
        console.print(references.encoded({"identities": page_data["identities"]}), markup=False, soft_wrap=True)
    except budget_core.InvalidCursorError as exc:
        fail(console, str(exc))

    for name in page.items:
        console.print(name, markup=False)
    if page.next_cursor is not None:
        console.print(f"More results - pass --cursor {page.next_cursor} to continue.", markup=False)


@app.command("order")
@reference_inputs("encounter")
def order_encounters(
    campaign: str | None = _campaign_option(),
) -> None:
    """Show every campaign encounter in deterministic dependency order."""
    campaign = _resolve_campaign(campaign, require_mutable=False)
    try:
        ordered = encounter_core.order_encounters(resolve_project_root(), campaign)
    except encounter_core.EncounterDependencyError as exc:
        fail(console, str(exc))
    if not ordered:
        console.print("No encounter files found.", markup=False)
        return

    identities = references.identity_order(
        resolve_project_root(),
        [{"name": item.name, "status": item.status, "depends_on": item.depends_on} for item in ordered],
        campaign,
    )
    console.print(
        references.encoded({"identities": [item["identity"] for item in identities]}), markup=False, soft_wrap=True
    )
    for item in ordered:
        dependencies = ", ".join(item.depends_on) or "(none)"
        console.print(f"{item.name} [{item.status}] depends_on: {dependencies}", markup=False)


@app.command("create")
@reference_inputs("encounter", create=True, mutable=True)
def create_encounter(
    name: str = typer.Argument(..., help="Encounter name (letters, numbers, underscores, hyphens, periods)."),
    campaign: str | None = _campaign_option(),
    body: str | None = typer.Option(
        None, "--body", "-b", help="Markdown body. Opens an editor if neither body option is supplied."
    ),
    body_file: str | None = typer.Option(
        None, "--body-file", metavar="PATH", help="UTF-8 body file; cannot be combined with --body/-b."
    ),
    kind: str = typer.Option(
        "scripted",
        "--kind",
        "-k",
        help="Encounter subtype: 'scripted' (default; Plan/Verification apply) or 'unscripted' (records "
        "already-done work; only Requirements/Rationale apply).",
    ),
) -> None:
    """Create a new encounter file."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        body = resolve_body_input(body, body_file)
        content = body if body is not None else edit_markdown(encounter_core.template_body(kind))
    except encounter_core.InvalidEncounterKindError as exc:
        fail(console, str(exc))

    try:
        path = encounter_core.create_encounter(resolve_project_root(), campaign, name, content, kind=kind)
    except (
        campaign_core.CampaignNotFoundError,
        encounter_core.InvalidEncounterNameError,
        encounter_core.InvalidEncounterKindError,
        encounter_core.EncounterAlreadyExistsError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Created {path}", markup=False)


@app.command("update")
@reference_inputs("encounter", mutable=True)
def update_encounter(
    name: str = typer.Argument(..., help="Encounter name to update."),
    campaign: str | None = _campaign_option(),
    body: str | None = typer.Option(
        None, "--body", "-b", help="Markdown body. Opens an editor if neither body option is supplied."
    ),
    body_file: str | None = typer.Option(
        None, "--body-file", metavar="PATH", help="UTF-8 body file; cannot be combined with --body/-b."
    ),
) -> None:
    """Update an existing encounter file's body. Only permitted while status is 'draft'."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        current = encounter_core.read_encounter(resolve_project_root(), campaign, name)
    except encounter_core.EncounterNotFoundError as exc:
        fail(console, str(exc))

    if current.status != "draft":
        fail(
            console,
            f"Encounter {name!r} is in status {current.status!r}; its content can only be replaced while in "
            "'draft' status. Use 'cac encounter record-message' to append additional context instead.",
        )

    body = resolve_body_input(body, body_file)
    content = body if body is not None else edit_markdown(current.body)
    try:
        path = encounter_core.update_encounter(resolve_project_root(), campaign, name, content)
    except (encounter_core.EncounterNotDraftError, GitIdentityError) as exc:
        fail(console, str(exc))

    console.print(f"Updated {path}", markup=False)


@app.command("delete")
@reference_inputs("encounter", mutable=True)
def delete_encounter(
    name: str = typer.Argument(..., help="Encounter name to delete."),
    campaign: str | None = _campaign_option(),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt."),
) -> None:
    """Delete an encounter file."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    if not yes:
        typer.confirm(f"Delete encounter {name!r}?", abort=True)

    try:
        path = encounter_core.delete_encounter(resolve_project_root(), campaign, name)
    except (encounter_core.EncounterNotFoundError, encounter_core.EncounterDependencyError) as exc:
        fail(console, str(exc))

    console.print(f"Deleted {path}", markup=False)


@app.command("review")
@reference_inputs("encounter", mutable=True)
def review_encounter(
    name: str = typer.Argument(..., help="Encounter name to review."),
    campaign: str | None = _campaign_option(),
    message: str = typer.Option(..., "--message", "-m", help="Lore-review result. Required."),
) -> None:
    """Move an encounter from 'draft' to 'reviewed' after a lore review. Requires at least one
    assigned region. Locks its content."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.review_encounter(resolve_project_root(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        encounter_core.EncounterMessageRequiredError,
        encounter_core.EncounterRegionRequiredError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Reviewed {name}; status is now reviewed.", markup=False)


@app.command("open")
@reference_inputs("encounter", mutable=True)
def open_encounter(
    name: str = typer.Argument(..., help="Encounter name to open."),
    campaign: str | None = _campaign_option(),
    message: str | None = typer.Option(None, "--message", "-m", help="Optional instructions or feedback."),
) -> None:
    """Move an encounter from 'reviewed' to 'open' and begin execution."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.open_encounter(resolve_project_root(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        encounter_core.EncounterDependenciesIncompleteError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Opened {name}.", markup=False)


@app.command("record-message")
@reference_inputs("encounter", mutable=True)
def record_message(
    name: str = typer.Argument(..., help="Encounter name to record a message on."),
    campaign: str | None = _campaign_option(),
    message: str = typer.Option(..., "--message", "-m", help="Message to append. Required."),
) -> None:
    """Append a message to an encounter without changing its status. Valid while 'reviewed' or 'open'."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.record_message(resolve_project_root(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        encounter_core.EncounterMessageRequiredError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Recorded message on {name}.", markup=False)


@app.command("complete")
@reference_inputs("encounter", mutable=True)
def complete_encounter(
    name: str = typer.Argument(..., help="Encounter name to complete."),
    campaign: str | None = _campaign_option(),
    message: str | None = typer.Option(None, "--message", "-m", help="Optional closing notes."),
) -> None:
    """Move an encounter from 'open' to 'completed' once verification passes."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.complete_encounter(resolve_project_root(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Completed {name}.", markup=False)


@app.command("abandon")
@reference_inputs("encounter", mutable=True)
def abandon_encounter(
    name: str = typer.Argument(..., help="Encounter name to abandon."),
    campaign: str | None = _campaign_option(),
    message: str = typer.Option(..., "--message", "-m", help="Reason for abandoning. Required."),
) -> None:
    """Abandon an encounter from 'draft', 'reviewed', or 'open'. Not available once 'completed'."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.abandon_encounter(resolve_project_root(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        encounter_core.EncounterMessageRequiredError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Abandoned {name}.", markup=False)


@app.command("assign-region")
@reference_inputs("encounter", mutable=True)
def assign_region(
    name: str = typer.Argument(..., help="Encounter name to assign."),
    region: str = typer.Argument(..., help="Region name to assign the encounter to."),
    campaign: str | None = _campaign_option(),
) -> None:
    """Assign an encounter to a region. An encounter may be assigned to one or more regions."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.assign_region(resolve_project_root(), campaign, name, region)
    except (
        encounter_core.EncounterNotFoundError,
        region_core.RegionNotFoundError,
        encounter_core.EncounterRegionMutationError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Assigned {name} to region {region}.", markup=False)


@app.command("unassign-region")
@reference_inputs("encounter", mutable=True)
def unassign_region(
    name: str = typer.Argument(..., help="Encounter name to unassign."),
    region: str = typer.Argument(..., help="Region name to unassign the encounter from."),
    campaign: str | None = _campaign_option(),
) -> None:
    """Unassign an encounter from a region."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.unassign_region(resolve_project_root(), campaign, name, region)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.EncounterRegionMutationError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Unassigned {name} from region {region}.", markup=False)


@app.command("assign-dependency")
@reference_inputs("encounter", mutable=True)
def assign_dependency(
    name: str = typer.Argument(..., help="Encounter that depends on the prerequisite."),
    dependency: str = typer.Argument(..., help="Direct prerequisite encounter name."),
    campaign: str | None = _campaign_option(),
) -> None:
    """Assign a direct prerequisite while the dependent encounter is draft."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.assign_dependency(resolve_project_root(), campaign, name, dependency)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterNameError,
        encounter_core.EncounterDependencyError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Assigned dependency {dependency} to encounter {name}.", markup=False)


@app.command("unassign-dependency")
@reference_inputs("encounter", mutable=True, remove=True)
def unassign_dependency(
    name: str = typer.Argument(..., help="Encounter whose dependency should be removed."),
    dependency: str = typer.Argument(..., help="Direct prerequisite encounter name."),
    campaign: str | None = _campaign_option(),
) -> None:
    """Unassign a direct prerequisite while the dependent encounter is draft."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.unassign_dependency(resolve_project_root(), campaign, name, dependency)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterNameError,
        encounter_core.EncounterDependencyError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Unassigned dependency {dependency} from encounter {name}.", markup=False)
