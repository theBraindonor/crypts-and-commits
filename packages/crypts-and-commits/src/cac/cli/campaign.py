from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail
from cac.core import campaign as campaign_core

app = typer.Typer(
    help=(
        "Manage campaign entries - long-running initiatives on the project, similar to an "
        "'Epic' in Jira-style work tracking. A campaign is expected to require many "
        "encounters, completed over time, before it is considered complete. Examples "
        "include 'Create the MVP', 'Add Payment Processing', or a version increment."
    )
)
console = Console()


@app.command("get")
def get_campaign(
    name: str = typer.Argument(..., help="Campaign name to show."),
) -> None:
    """Show a campaign file's frontmatter and body."""
    try:
        metadata, body = campaign_core.read_metadata(Path.cwd(), name)
    except campaign_core.CampaignNotFoundError as exc:
        fail(console, str(exc))

    for key, value in metadata.items():
        console.print(f"[bold]{key}[/bold]: {value}")
    console.print()
    console.print(body)


@app.command("list")
def list_campaigns() -> None:
    """List the campaign files in .sourcebook/campaigns."""
    names = campaign_core.list_campaigns(Path.cwd())
    if not names:
        console.print("No campaign files found.")
        return

    for name in names:
        console.print(name)


@app.command("create")
def create_campaign(
    name: str = typer.Argument(..., help="Campaign name (letters, numbers, underscores, hyphens, periods)."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Create a new campaign file."""
    content = body if body is not None else edit_markdown(campaign_core.template_body())

    try:
        path = campaign_core.create_campaign(Path.cwd(), name, content)
    except (campaign_core.InvalidCampaignNameError, campaign_core.CampaignAlreadyExistsError) as exc:
        fail(console, str(exc))

    console.print(f"Created [bold green]{path}[/bold green]")


@app.command("update")
def update_campaign(
    name: str = typer.Argument(..., help="Campaign name to update."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Update an existing campaign file's body."""
    try:
        current = campaign_core.read_campaign(Path.cwd(), name)
    except campaign_core.CampaignNotFoundError as exc:
        fail(console, str(exc))

    content = body if body is not None else edit_markdown(current.body)
    path = campaign_core.update_campaign(Path.cwd(), name, content)
    console.print(f"Updated [bold green]{path}[/bold green]")


@app.command("delete")
def delete_campaign(
    name: str = typer.Argument(..., help="Campaign name to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt."),
) -> None:
    """Delete a campaign file."""
    if not yes:
        typer.confirm(f"Delete campaign {name!r}?", abort=True)

    try:
        path = campaign_core.delete_campaign(Path.cwd(), name)
    except campaign_core.CampaignNotFoundError as exc:
        fail(console, str(exc))

    console.print(f"Deleted [bold green]{path}[/bold green]")


@app.command("set-status")
def set_status(
    name: str = typer.Argument(..., help="Campaign name to update."),
    status: str = typer.Argument(..., help="New status: draft, open, completed, or abandoned."),
) -> None:
    """Set a campaign's status."""
    try:
        campaign_core.set_status(Path.cwd(), name, status)
    except (campaign_core.CampaignNotFoundError, campaign_core.InvalidCampaignStatusError) as exc:
        fail(console, str(exc))

    console.print(f"Set [bold]{name}[/bold] status to [bold]{status}[/bold].")
