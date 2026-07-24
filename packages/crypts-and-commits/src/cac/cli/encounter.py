from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail
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
        "'complete' messages or 'record-message'."
    )
)
console = Console()


@app.command("get")
def get_encounter(
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to show."),
) -> None:
    """Show an encounter file's frontmatter and body."""
    try:
        metadata, body = encounter_core.read_metadata(Path.cwd(), campaign, name)
    except encounter_core.EncounterNotFoundError as exc:
        fail(console, str(exc))

    for key, value in metadata.items():
        console.print(f"[bold]{key}[/bold]: {value}")
    console.print()
    console.print(body, markup=False)


@app.command("list")
def list_encounters(
    campaign: str = typer.Argument(..., help="Campaign the encounters belong to."),
) -> None:
    """List the encounter files in .sourcebook/encounters/<campaign>."""
    names = encounter_core.list_encounters(Path.cwd(), campaign)
    if not names:
        console.print("No encounter files found.")
        return

    for name in names:
        console.print(name)


@app.command("create")
def create_encounter(
    campaign: str = typer.Argument(..., help="Campaign to assign the encounter to."),
    name: str = typer.Argument(..., help="Encounter name (letters, numbers, underscores, hyphens, periods)."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Create a new encounter file."""
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
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to update."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Update an existing encounter file's body. Only permitted while status is 'draft'."""
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
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt."),
) -> None:
    """Delete an encounter file."""
    if not yes:
        typer.confirm(f"Delete encounter {name!r}?", abort=True)

    try:
        path = encounter_core.delete_encounter(Path.cwd(), campaign, name)
    except encounter_core.EncounterNotFoundError as exc:
        fail(console, str(exc))

    console.print(f"Deleted [bold green]{path}[/bold green]")


@app.command("review")
def review_encounter(
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to review."),
    message: str = typer.Option(..., "--message", "-m", help="Lore-review result. Required."),
) -> None:
    """Move an encounter from 'draft' to 'reviewed' after a lore review. Locks its content."""
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
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to open."),
    message: str | None = typer.Option(None, "--message", "-m", help="Optional instructions or feedback."),
) -> None:
    """Move an encounter from 'reviewed' to 'open' and begin execution."""
    try:
        encounter_core.open_encounter(Path.cwd(), campaign, name, message)
    except (
        encounter_core.EncounterNotFoundError,
        encounter_core.InvalidEncounterTransitionError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Opened [bold]{name}[/bold].")


@app.command("record-message")
def record_message(
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to record a message on."),
    message: str = typer.Option(..., "--message", "-m", help="Message to append. Required."),
) -> None:
    """Append a message to an encounter without changing its status. Valid while 'reviewed' or 'open'."""
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
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to complete."),
    message: str | None = typer.Option(None, "--message", "-m", help="Optional closing notes."),
) -> None:
    """Move an encounter from 'open' to 'completed' once verification passes."""
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
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to abandon."),
    message: str = typer.Option(..., "--message", "-m", help="Reason for abandoning. Required."),
) -> None:
    """Abandon an encounter from 'draft', 'reviewed', or 'open'. Not available once 'completed'."""
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
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to assign."),
    region: str = typer.Argument(..., help="Region name to assign the encounter to."),
) -> None:
    """Assign an encounter to a region. An encounter may be assigned to one or more regions."""
    try:
        encounter_core.assign_region(Path.cwd(), campaign, name, region)
    except (encounter_core.EncounterNotFoundError, region_core.RegionNotFoundError, GitIdentityError) as exc:
        fail(console, str(exc))

    console.print(f"Assigned [bold]{name}[/bold] to region [bold]{region}[/bold].")


@app.command("unassign-region")
def unassign_region(
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to unassign."),
    region: str = typer.Argument(..., help="Region name to unassign the encounter from."),
) -> None:
    """Unassign an encounter from a region."""
    try:
        encounter_core.unassign_region(Path.cwd(), campaign, name, region)
    except (encounter_core.EncounterNotFoundError, GitIdentityError) as exc:
        fail(console, str(exc))

    console.print(f"Unassigned [bold]{name}[/bold] from region [bold]{region}[/bold].")
