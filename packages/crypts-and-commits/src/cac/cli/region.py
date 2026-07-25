from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail
from cac.core import region as region_core
from cac.core.config import SUMMARY_KEY

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
        metadata, body = region_core.read_metadata(Path.cwd(), name)
        summary = region_core.read_summary(Path.cwd(), name)
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
    console.print(body, markup=False)


@app.command("list")
def list_regions() -> None:
    """List the region files in .sourcebook/region."""
    names = region_core.list_regions(Path.cwd())
    if not names:
        console.print("No region files found.")
        return

    for name in names:
        console.print(name)


@app.command("create")
def create_region(
    name: str = typer.Argument(..., help="Region name (letters, numbers, underscores, hyphens, periods)."),
    path_value: str = typer.Option("", "--path", "-p", help="Path within the repository this region covers."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Create a new region file."""
    content = body if body is not None else edit_markdown(region_core.template_body())

    try:
        path = region_core.create_region(Path.cwd(), name, content, path_value)
    except (region_core.InvalidRegionNameError, region_core.RegionAlreadyExistsError) as exc:
        fail(console, str(exc))

    console.print(f"Created [bold green]{path}[/bold green]")


@app.command("update")
def update_region(
    name: str = typer.Argument(..., help="Region name to update."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Update an existing region file's body."""
    try:
        current = region_core.read_region(Path.cwd(), name)
    except region_core.RegionNotFoundError as exc:
        fail(console, str(exc))

    content = body if body is not None else edit_markdown(current.body)
    path = region_core.update_region(Path.cwd(), name, content)
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
        path = region_core.delete_region(Path.cwd(), name)
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
        region_core.set_summary(Path.cwd(), name, summary)
    except region_core.RegionNotFoundError as exc:
        fail(console, str(exc))
    except region_core.SummaryTooLongError as exc:
        fail(console, str(exc))

    console.print(f"Set summary on [bold]{name}[/bold].")


@app.command("set-path")
def set_path(
    name: str = typer.Argument(..., help="Region name to update."),
    path_value: str = typer.Argument(..., help="Path within the repository this region covers."),
) -> None:
    """Set a region's path."""
    try:
        region_core.set_path(Path.cwd(), name, path_value)
    except region_core.RegionNotFoundError as exc:
        fail(console, str(exc))

    console.print(f"Set [bold]{name}[/bold] path to [bold]{path_value}[/bold].")
