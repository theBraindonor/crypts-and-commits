from pathlib import Path
from typing import Any, NoReturn

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail
from cac.core import budget as budget_core
from cac.core import campaign as campaign_core
from cac.core import encounter as encounter_core
from cac.core import region as region_core
from cac.core.git_utils import GitIdentityError

app = typer.Typer(
    help=(
        "Manage encounter entries - a concrete unit of work within a campaign, representing "
        "a plan the AI agent is expected to execute. An encounter moves through a fixed "
        "lifecycle: 'draft' (being planned; the only status in which its content may be "
        "replaced with 'update') -> 'reviewed' (via 'review', after a lore check; locks the "
        "content) -> 'open' (via 'open'; work begins) -> 'completed' (via 'complete', after "
        "verification passes). It may instead be marked 'abandoned' (via 'abandon') from "
        "'draft', 'reviewed', or 'open' - but not once 'completed'. Once past 'draft', content "
        "can no longer be replaced, only appended to via the 'review'/'abandon'/'open'/"
        "'complete' messages or 'record-message'. Dependencies may be changed while an "
        "encounter is 'draft' or 'reviewed'; all must be completed before it can open. "
        "The campaign defaults to the active (open) campaign; use --campaign to target another one."
    )
)
console = Console()

_CAMPAIGN_HELP = "Campaign to act on. Defaults to the active (open) campaign."


def _campaign_option() -> Any:
    return typer.Option(None, "--campaign", "-c", help=_CAMPAIGN_HELP)


def _resolve_campaign(campaign: str | None, *, require_mutable: bool) -> str | NoReturn:
    """Resolve the campaign to act on, failing with a clear message if none is active, the named
    campaign does not exist, or (when mutating) it is completed/abandoned."""
    try:
        return campaign_core.resolve_campaign(Path.cwd(), campaign, require_mutable=require_mutable)
    except (
        campaign_core.NoActiveCampaignError,
        campaign_core.CampaignNotFoundError,
        campaign_core.CampaignNotMutableError,
    ) as exc:
        fail(console, str(exc))


@app.command("get")
def get_encounter(
    name: str = typer.Argument(..., help="Encounter name to show."),
    campaign: str | None = _campaign_option(),
) -> None:
    """Show an encounter file's frontmatter and body."""
    campaign = _resolve_campaign(campaign, require_mutable=False)
    try:
        metadata, body = encounter_core.read_metadata(Path.cwd(), campaign, name)
    except encounter_core.EncounterNotFoundError as exc:
        fail(console, str(exc))

    for key, value in metadata.items():
        console.print(f"[bold]{key}[/bold]: {value}")
    console.print()
    body = budget_core.truncate_body(body, encounter_core.encounter_path(Path.cwd(), campaign, name))
    console.print(body, markup=False, soft_wrap=True)


@app.command("list")
def list_encounters(
    campaign: str | None = _campaign_option(),
    cursor: str | None = typer.Option(None, "--cursor", help="Resume from a previous page's cursor."),
) -> None:
    """List the encounter files in a campaign, oldest-updated first, paged under the response
    budget."""
    campaign = _resolve_campaign(campaign, require_mutable=False)
    names = encounter_core.list_encounters(Path.cwd(), campaign)
    if not names:
        console.print("No encounter files found.")
        return

    try:
        page = budget_core.paginate(names, cursor)
    except budget_core.InvalidCursorError as exc:
        fail(console, str(exc))

    for name in page.items:
        console.print(name)
    if page.next_cursor is not None:
        console.print(f"[dim]More results - pass --cursor {page.next_cursor} to continue.[/dim]")


@app.command("order")
def order_encounters(
    campaign: str | None = _campaign_option(),
) -> None:
    """Show every campaign encounter in deterministic dependency order."""
    campaign = _resolve_campaign(campaign, require_mutable=False)
    try:
        ordered = encounter_core.order_encounters(Path.cwd(), campaign)
    except encounter_core.EncounterDependencyError as exc:
        fail(console, str(exc))
    if not ordered:
        console.print("No encounter files found.")
        return

    for item in ordered:
        dependencies = ", ".join(item.depends_on) or "(none)"
        console.print(f"{item.name} [{item.status}] depends_on: {dependencies}", markup=False)


@app.command("create")
def create_encounter(
    name: str = typer.Argument(..., help="Encounter name (letters, numbers, underscores, hyphens, periods)."),
    campaign: str | None = _campaign_option(),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Create a new encounter file."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    content = body if body is not None else edit_markdown(encounter_core.template_body())

    try:
        path = encounter_core.create_encounter(Path.cwd(), campaign, name, content)
    except (
        campaign_core.CampaignNotFoundError,
        encounter_core.InvalidEncounterNameError,
        encounter_core.EncounterAlreadyExistsError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Created [bold green]{path}[/bold green]")


@app.command("update")
def update_encounter(
    name: str = typer.Argument(..., help="Encounter name to update."),
    campaign: str | None = _campaign_option(),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Update an existing encounter file's body. Only permitted while status is 'draft'."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        current = encounter_core.read_encounter(Path.cwd(), campaign, name)
    except encounter_core.EncounterNotFoundError as exc:
        fail(console, str(exc))

    if current.status != "draft":
        fail(
            console,
            f"Encounter {name!r} is in status {current.status!r}; its content can only be replaced while in "
            "'draft' status. Use 'cac encounter record-message' to append additional context instead.",
        )

    content = body if body is not None else edit_markdown(current.body)
    try:
        path = encounter_core.update_encounter(Path.cwd(), campaign, name, content)
    except (encounter_core.EncounterNotDraftError, GitIdentityError) as exc:
        fail(console, str(exc))

    console.print(f"Updated [bold green]{path}[/bold green]")


@app.command("delete")
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
        path = encounter_core.delete_encounter(Path.cwd(), campaign, name)
    except (encounter_core.EncounterNotFoundError, encounter_core.EncounterDependencyError) as exc:
        fail(console, str(exc))

    console.print(f"Deleted [bold green]{path}[/bold green]")


@app.command("review")
def review_encounter(
    name: str = typer.Argument(..., help="Encounter name to review."),
    campaign: str | None = _campaign_option(),
    message: str = typer.Option(..., "--message", "-m", help="Lore-review result. Required."),
) -> None:
    """Move an encounter from 'draft' to 'reviewed' after a lore review. Locks its content."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.review_encounter(Path.cwd(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        encounter_core.EncounterMessageRequiredError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Reviewed [bold]{name}[/bold]; status is now [bold]reviewed[/bold].")


@app.command("open")
def open_encounter(
    name: str = typer.Argument(..., help="Encounter name to open."),
    campaign: str | None = _campaign_option(),
    message: str | None = typer.Option(None, "--message", "-m", help="Optional instructions or feedback."),
) -> None:
    """Move an encounter from 'reviewed' to 'open' and begin execution."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.open_encounter(Path.cwd(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        encounter_core.EncounterDependenciesIncompleteError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Opened [bold]{name}[/bold].")


@app.command("record-message")
def record_message(
    name: str = typer.Argument(..., help="Encounter name to record a message on."),
    campaign: str | None = _campaign_option(),
    message: str = typer.Option(..., "--message", "-m", help="Message to append. Required."),
) -> None:
    """Append a message to an encounter without changing its status. Valid while 'reviewed' or 'open'."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.record_message(Path.cwd(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        encounter_core.EncounterMessageRequiredError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Recorded message on [bold]{name}[/bold].")


@app.command("complete")
def complete_encounter(
    name: str = typer.Argument(..., help="Encounter name to complete."),
    campaign: str | None = _campaign_option(),
    message: str | None = typer.Option(None, "--message", "-m", help="Optional closing notes."),
) -> None:
    """Move an encounter from 'open' to 'completed' once verification passes."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.complete_encounter(Path.cwd(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Completed [bold]{name}[/bold].")


@app.command("abandon")
def abandon_encounter(
    name: str = typer.Argument(..., help="Encounter name to abandon."),
    campaign: str | None = _campaign_option(),
    message: str = typer.Option(..., "--message", "-m", help="Reason for abandoning. Required."),
) -> None:
    """Abandon an encounter from 'draft', 'reviewed', or 'open'. Not available once 'completed'."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.abandon_encounter(Path.cwd(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        encounter_core.EncounterMessageRequiredError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Abandoned [bold]{name}[/bold].")


@app.command("assign-region")
def assign_region(
    name: str = typer.Argument(..., help="Encounter name to assign."),
    region: str = typer.Argument(..., help="Region name to assign the encounter to."),
    campaign: str | None = _campaign_option(),
) -> None:
    """Assign an encounter to a region. An encounter may be assigned to one or more regions."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.assign_region(Path.cwd(), campaign, name, region)
    except (encounter_core.EncounterNotFoundError, region_core.RegionNotFoundError, GitIdentityError) as exc:
        fail(console, str(exc))

    console.print(f"Assigned [bold]{name}[/bold] to region [bold]{region}[/bold].")


@app.command("unassign-region")
def unassign_region(
    name: str = typer.Argument(..., help="Encounter name to unassign."),
    region: str = typer.Argument(..., help="Region name to unassign the encounter from."),
    campaign: str | None = _campaign_option(),
) -> None:
    """Unassign an encounter from a region."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.unassign_region(Path.cwd(), campaign, name, region)
    except (encounter_core.EncounterNotFoundError, GitIdentityError) as exc:
        fail(console, str(exc))

    console.print(f"Unassigned [bold]{name}[/bold] from region [bold]{region}[/bold].")


@app.command("assign-dependency")
def assign_dependency(
    name: str = typer.Argument(..., help="Encounter that depends on the prerequisite."),
    dependency: str = typer.Argument(..., help="Direct prerequisite encounter name."),
    campaign: str | None = _campaign_option(),
) -> None:
    """Assign a direct prerequisite while the dependent encounter is draft or reviewed."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.assign_dependency(Path.cwd(), campaign, name, dependency)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterNameError,
        encounter_core.EncounterDependencyError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Assigned dependency [bold]{dependency}[/bold] to encounter [bold]{name}[/bold].")


@app.command("unassign-dependency")
def unassign_dependency(
    name: str = typer.Argument(..., help="Encounter whose dependency should be removed."),
    dependency: str = typer.Argument(..., help="Direct prerequisite encounter name."),
    campaign: str | None = _campaign_option(),
) -> None:
    """Unassign a direct prerequisite while the dependent encounter is draft or reviewed."""
    campaign = _resolve_campaign(campaign, require_mutable=True)
    try:
        encounter_core.unassign_dependency(Path.cwd(), campaign, name, dependency)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterNameError,
        encounter_core.EncounterDependencyError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Unassigned dependency [bold]{dependency}[/bold] from encounter [bold]{name}[/bold].")
