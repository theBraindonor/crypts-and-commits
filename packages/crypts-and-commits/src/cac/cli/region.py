import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail
from cac.core import budget as budget_core
from cac.core import region as region_core
from cac.core.config import SUMMARY_KEY
from cac.core.git_utils import GitIdentityError
from cac.core.paths import resolve_project_root

app = typer.Typer(
    help=(
        "Manage region entries - paths within the repository that need their own "
        "documentation and that specific lore rules can be applied to. For example, a web "
        "application's world might have a 'frontend' region and a 'backend' region, each "
        "with its own tech stack, tooling, and conventions."
    )
)
console = Console()


@app.command("get")
def get_region(
    name: str = typer.Argument(..., help="Region name to show."),
) -> None:
    """Show a region file's frontmatter and body."""
    try:
        metadata, body = region_core.read_metadata(resolve_project_root(), name)
        summary = region_core.read_summary(resolve_project_root(), name)
    except region_core.RegionNotFoundError as exc:
        fail(console, str(exc))

    # Keep the summary out of the markup=True loop below; it is stored content and must be
    # rendered with markup=False so bracketed text is not silently stripped.
    metadata.pop(SUMMARY_KEY, None)
    for key, value in metadata.items():
        console.print(f"[bold]{key}[/bold]: {value}")
    console.print("[bold]summary[/bold]:", end=" ")
    console.print(summary, markup=False)
    console.print()
    body = budget_core.truncate_body(body, region_core.region_path(resolve_project_root(), name))
    console.print(body, markup=False, soft_wrap=True)


@app.command("list")
def list_regions(
    cursor: str | None = typer.Option(None, "--cursor", help="Resume from a previous page's cursor."),
) -> None:
    """List the region files in .sourcebook/region, paged under the response budget."""
    names = region_core.list_regions(resolve_project_root())
    if not names:
        console.print("No region files found.")
        return

    try:
        page = budget_core.paginate(names, cursor)
    except budget_core.InvalidCursorError as exc:
        fail(console, str(exc))

    for name in page.items:
        console.print(name)
    if page.next_cursor is not None:
        console.print(f"[dim]More results - pass --cursor {page.next_cursor} to continue.[/dim]")


@app.command("create")
def create_region(
    name: str = typer.Argument(..., help="Region name (letters, numbers, underscores, hyphens, periods)."),
    path_value: str = typer.Option("", "--path", "-p", help="Path within the repository this region covers."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
    summary: str | None = typer.Option(
        None, "--summary", "-s", help="Short routing summary (max 500 characters). Required alongside the body."
    ),
) -> None:
    """Create a new region file."""
    if summary is None:
        fail(console, "A summary is required: pass --summary/-s so the new body is stored with a current summary.")

    content = body if body is not None else edit_markdown(region_core.template_body())

    try:
        path = region_core.create_region(resolve_project_root(), name, content, summary, path_value)
    except (
        region_core.InvalidRegionNameError,
        region_core.RegionAlreadyExistsError,
        region_core.SummaryTooLongError,
        GitIdentityError,
    ) as exc:
        fail(console, str(exc))

    console.print(f"Created [bold green]{path}[/bold green]")


@app.command("update")
def update_region(
    name: str = typer.Argument(..., help="Region name to update."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
    summary: str | None = typer.Option(
        None, "--summary", "-s", help="Short routing summary (max 500 characters). Required alongside the body."
    ),
) -> None:
    """Update an existing region file's body."""
    if summary is None:
        fail(console, "A summary is required: pass --summary/-s so the edited body is stored with a current summary.")

    try:
        current = region_core.read_region(resolve_project_root(), name)
    except region_core.RegionNotFoundError as exc:
        fail(console, str(exc))

    content = body if body is not None else edit_markdown(current.body)

    try:
        path = region_core.update_region(resolve_project_root(), name, content, summary)
    except (region_core.SummaryTooLongError, GitIdentityError) as exc:
        fail(console, str(exc))

    console.print(f"Updated [bold green]{path}[/bold green]")


@app.command("delete")
def delete_region(
    name: str = typer.Argument(..., help="Region name to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt."),
) -> None:
    """Delete a region file."""
    if not yes:
        typer.confirm(f"Delete region {name!r}?", abort=True)

    try:
        path = region_core.delete_region(resolve_project_root(), name)
    except region_core.RegionNotFoundError as exc:
        fail(console, str(exc))

    console.print(f"Deleted [bold green]{path}[/bold green]")


@app.command("set-summary")
def set_summary(
    name: str = typer.Argument(..., help="Region name to update."),
    summary: str = typer.Argument(..., help="Short routing summary (max 500 characters)."),
) -> None:
    """Set a region's summary."""
    try:
        region_core.set_summary(resolve_project_root(), name, summary)
    except (region_core.RegionNotFoundError, region_core.SummaryTooLongError, GitIdentityError) as exc:
        fail(console, str(exc))

    console.print(f"Set summary on [bold]{name}[/bold].")


@app.command("set-path")
def set_path(
    name: str = typer.Argument(..., help="Region name to update."),
    path_value: str = typer.Argument(..., help="Path within the repository this region covers."),
) -> None:
    """Set a region's path."""
    try:
        region_core.set_path(resolve_project_root(), name, path_value)
    except (region_core.RegionNotFoundError, GitIdentityError) as exc:
        fail(console, str(exc))

    console.print(f"Set [bold]{name}[/bold] path to [bold]{path_value}[/bold].")
