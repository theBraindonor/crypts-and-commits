from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail
from cac.core import region as region_core

app = typer.Typer(help="Manage region files describing places in the project's world.")
console = Console()


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
    name: str = typer.Argument(..., help="Region name (letters, numbers, underscores, hyphens)."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Create a new region file."""
    content = body if body is not None else edit_markdown(region_core.template_body())

    try:
        path = region_core.create_region(Path.cwd(), name, content)
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
