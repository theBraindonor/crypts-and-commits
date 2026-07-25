from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail
from cac.core import budget as budget_core
from cac.core import campaign as campaign_core
from cac.core.git_utils import GitIdentityError

app = typer.Typer(
    help=(
        "Manage campaign entries - long-running initiatives on the project, similar to an "
        "'Epic' in Jira-style work tracking. A campaign is expected to require many "
        "encounters, completed over time, before it is considered complete. Examples "
        "include 'Create the MVP', 'Add Payment Processing', or a version increment. A "
        "campaign moves through a fixed lifecycle: 'draft' (just created) -> 'open' (via "
        "'open'; only one campaign may be open at a time) -> 'paused' (via 'pause') or back "
        "to 'open' again -> 'completed' (via 'complete', from 'open' or 'paused'). It may "
        "instead be 'abandoned' (via 'abandon') from 'draft', 'open', or 'paused' - but not "
        "once 'completed'. 'pause', 'complete', and 'abandon' all fail while the campaign "
        "still has an open encounter."
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
    body = budget_core.truncate_body(body, campaign_core.campaign_path(Path.cwd(), name))
    console.print(body, markup=False, soft_wrap=True)


@app.command("list")
def list_campaigns(
    cursor: str | None = typer.Option(None, "--cursor", help="Resume from a previous page's cursor."),
) -> None:
    """List the campaign files in .sourcebook/campaigns, with their current status, paged under
    the response budget."""
    entries = campaign_core.list_campaigns_with_status(Path.cwd())
    if not entries:
        console.print("No campaign files found.")
        return

    try:
        page = budget_core.paginate(entries, cursor, render=lambda entry: f"{entry[0]} ({entry[1]})")
    except budget_core.InvalidCursorError as exc:
        fail(console, str(exc))

    for name, status in page.items:
        console.print(f"{name} ({status})")
    if page.next_cursor is not None:
        console.print(f"[dim]More results - pass --cursor {page.next_cursor} to continue.[/dim]")


@app.command("create")
def create_campaign(
    name: str = typer.Argument(..., help="Campaign name (letters, numbers, underscores, hyphens, periods)."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Create a new campaign file."""
    content = body if body is not None else edit_markdown(campaign_core.template_body())

    try:
        path = campaign_core.create_campaign(Path.cwd(), name, content)
    except (campaign_core.InvalidCampaignNameError, campaign_core.CampaignAlreadyExistsError, GitIdentityError) as exc:
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
    try:
        path = campaign_core.update_campaign(Path.cwd(), name, content)
    except GitIdentityError as exc:
        fail(console, str(exc))

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


@app.command("open")
def open_campaign(
    name: str = typer.Argument(..., help="Campaign name to open."),
) -> None:
    """Move a campaign from 'draft' or 'paused' to 'open'. Only one campaign may be open at a
    time."""
    try:
        campaign_core.open_campaign(Path.cwd(), name)
    except (
        campaign_core.CampaignNotFoundError,
        campaign_core.InvalidCampaignTransitionError,
        campaign_core.AnotherCampaignOpenError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Opened [bold]{name}[/bold].")


@app.command("pause")
def pause_campaign(
    name: str = typer.Argument(..., help="Campaign name to pause."),
) -> None:
    """Move a campaign from 'open' to 'paused'. Fails if it has an open encounter."""
    try:
        campaign_core.pause_campaign(Path.cwd(), name)
    except (
        campaign_core.CampaignNotFoundError,
        campaign_core.InvalidCampaignTransitionError,
        campaign_core.CampaignHasOpenEncountersError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Paused [bold]{name}[/bold].")


@app.command("complete")
def complete_campaign(
    name: str = typer.Argument(..., help="Campaign name to complete."),
) -> None:
    """Move a campaign from 'open' or 'paused' to 'completed'. Fails if it has an open
    encounter."""
    try:
        campaign_core.complete_campaign(Path.cwd(), name)
    except (
        campaign_core.CampaignNotFoundError,
        campaign_core.InvalidCampaignTransitionError,
        campaign_core.CampaignHasOpenEncountersError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Completed [bold]{name}[/bold].")


@app.command("abandon")
def abandon_campaign(
    name: str = typer.Argument(..., help="Campaign name to abandon."),
) -> None:
    """Move a campaign from 'draft', 'open', or 'paused' to 'abandoned'. Fails if it has an open
    encounter."""
    try:
        campaign_core.abandon_campaign(Path.cwd(), name)
    except (
        campaign_core.CampaignNotFoundError,
        campaign_core.InvalidCampaignTransitionError,
        campaign_core.CampaignHasOpenEncountersError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Abandoned [bold]{name}[/bold].")
