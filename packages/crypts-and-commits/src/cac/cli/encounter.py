from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail
from cac.core import campaign as campaign_core
from cac.core import encounter as encounter_core
from cac.core import region as region_core

app = typer.Typer(
    help=(
        "Manage encounter entries - a concrete unit of work within a campaign, representing "
        "a plan the AI agent is expected to execute. An encounter starts in the 'draft' "
        "status while it is being documented and planned. Once it has passed all applicable "
        "lore checks (world lore and the lore of any region it is assigned to) and the user "
        "has approved it, it moves to 'open' and the agent begins the work. Once all work is "
        "finished and verification has passed, the agent confirms with the user before "
        "marking it 'completed'. An encounter may be marked 'abandoned' at any time, for any "
        "reason."
    )
)
console = Console()


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
    name: str = typer.Argument(..., help="Encounter name (letters, numbers, underscores, hyphens)."),
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
    ) as exc:
        fail(console, str(exc))

    console.print(f"Created [bold green]{path}[/bold green]")


@app.command("update")
def update_encounter(
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to update."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Update an existing encounter file's body."""
    try:
        current = encounter_core.read_encounter(Path.cwd(), campaign, name)
    except encounter_core.EncounterNotFoundError as exc:
        fail(console, str(exc))

    content = body if body is not None else edit_markdown(current.body)
    path = encounter_core.update_encounter(Path.cwd(), campaign, name, content)
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


@app.command("set-status")
def set_status(
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to update."),
    status: str = typer.Argument(..., help="New status: draft, open, completed, or abandoned."),
) -> None:
    """Set an encounter's status."""
    try:
        encounter_core.set_status(Path.cwd(), campaign, name, status)
    except (encounter_core.EncounterNotFoundError, encounter_core.InvalidEncounterStatusError) as exc:
        fail(console, str(exc))

    console.print(f"Set [bold]{name}[/bold] status to [bold]{status}[/bold].")


@app.command("assign-region")
def assign_region(
    campaign: str = typer.Argument(..., help="Campaign the encounter belongs to."),
    name: str = typer.Argument(..., help="Encounter name to assign."),
    region: str = typer.Argument(..., help="Region name to assign the encounter to."),
) -> None:
    """Assign an encounter to a region. An encounter may be assigned to one or more regions."""
    try:
        encounter_core.assign_region(Path.cwd(), campaign, name, region)
    except (encounter_core.EncounterNotFoundError, region_core.RegionNotFoundError) as exc:
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
    except encounter_core.EncounterNotFoundError as exc:
        fail(console, str(exc))

    console.print(f"Unassigned [bold]{name}[/bold] from region [bold]{region}[/bold].")
