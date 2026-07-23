from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail
from cac.core import lore as lore_core
from cac.core import region as region_core
from cac.core import world as world_core

app = typer.Typer(
    help=(
        "Manage lore entries - standards, conventions, and best practices to apply to the "
        "project. Lore is used to review encounters before work on them begins. Lore assigned "
        "to the world is global and applies to every encounter; otherwise, a lore entry only "
        "applies to an encounter when it is assigned to a region the encounter takes place in."
    )
)
console = Console()


@app.command("get")
def get_lore(
    name: str = typer.Argument(..., help="Lore name to show."),
) -> None:
    """Show a lore file's frontmatter and body."""
    try:
        metadata, body = lore_core.read_metadata(Path.cwd(), name)
    except lore_core.LoreNotFoundError as exc:
        fail(console, str(exc))

    for key, value in metadata.items():
        console.print(f"[bold]{key}[/bold]: {value}")
    console.print()
    console.print(body)


@app.command("list")
def list_lore() -> None:
    """List the lore files in .sourcebook/lore."""
    names = lore_core.list_lore(Path.cwd())
    if not names:
        console.print("No lore files found.")
        return

    for name in names:
        console.print(name)


@app.command("create")
def create_lore(
    name: str = typer.Argument(..., help="Lore name (letters, numbers, underscores, hyphens)."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Create a new lore file."""
    content = body if body is not None else edit_markdown(lore_core.template_body())

    try:
        path = lore_core.create_lore(Path.cwd(), name, content)
    except (lore_core.InvalidLoreNameError, lore_core.LoreAlreadyExistsError) as exc:
        fail(console, str(exc))

    console.print(f"Created [bold green]{path}[/bold green]")


@app.command("update")
def update_lore(
    name: str = typer.Argument(..., help="Lore name to update."),
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Update an existing lore file's body."""
    try:
        current = lore_core.read_lore(Path.cwd(), name)
    except lore_core.LoreNotFoundError as exc:
        fail(console, str(exc))

    content = body if body is not None else edit_markdown(current.body)
    path = lore_core.update_lore(Path.cwd(), name, content)
    console.print(f"Updated [bold green]{path}[/bold green]")


@app.command("delete")
def delete_lore(
    name: str = typer.Argument(..., help="Lore name to delete."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirmation prompt."),
) -> None:
    """Delete a lore file."""
    if not yes:
        typer.confirm(f"Delete lore {name!r}?", abort=True)

    try:
        path = lore_core.delete_lore(Path.cwd(), name)
    except lore_core.LoreNotFoundError as exc:
        fail(console, str(exc))

    console.print(f"Deleted [bold green]{path}[/bold green]")


@app.command("assign-world")
def assign_world(
    name: str = typer.Argument(..., help="Lore name to assign to the world."),
) -> None:
    """Assign a lore file to the world."""
    try:
        world_core.assign_lore(Path.cwd(), name)
    except (world_core.WorldNotFoundError, lore_core.LoreNotFoundError) as exc:
        fail(console, str(exc))

    console.print(f"Assigned [bold]{name}[/bold] to the world.")


@app.command("unassign-world")
def unassign_world(
    name: str = typer.Argument(..., help="Lore name to unassign from the world."),
) -> None:
    """Unassign a lore file from the world."""
    try:
        world_core.unassign_lore(Path.cwd(), name)
    except (world_core.WorldNotFoundError, lore_core.LoreNotFoundError) as exc:
        fail(console, str(exc))

    console.print(f"Unassigned [bold]{name}[/bold] from the world.")


@app.command("assign-region")
def assign_region(
    name: str = typer.Argument(..., help="Lore name to assign."),
    region: str = typer.Argument(..., help="Region name to assign the lore to."),
) -> None:
    """Assign a lore file to a region."""
    try:
        region_core.assign_lore(Path.cwd(), region, name)
    except (region_core.RegionNotFoundError, lore_core.LoreNotFoundError) as exc:
        fail(console, str(exc))

    console.print(f"Assigned [bold]{name}[/bold] to region [bold]{region}[/bold].")


@app.command("unassign-region")
def unassign_region(
    name: str = typer.Argument(..., help="Lore name to unassign."),
    region: str = typer.Argument(..., help="Region name to unassign the lore from."),
) -> None:
    """Unassign a lore file from a region."""
    try:
        region_core.unassign_lore(Path.cwd(), region, name)
    except (region_core.RegionNotFoundError, lore_core.LoreNotFoundError) as exc:
        fail(console, str(exc))

    console.print(f"Unassigned [bold]{name}[/bold] from region [bold]{region}[/bold].")


@app.command("enable")
def enable_lore(
    name: str = typer.Argument(..., help="Lore name to enable."),
) -> None:
    """Enable a lore file."""
    try:
        lore_core.set_enabled(Path.cwd(), name, True)
    except lore_core.LoreNotFoundError as exc:
        fail(console, str(exc))

    console.print(f"Enabled [bold]{name}[/bold].")


@app.command("disable")
def disable_lore(
    name: str = typer.Argument(..., help="Lore name to disable."),
) -> None:
    """Disable a lore file."""
    try:
        lore_core.set_enabled(Path.cwd(), name, False)
    except lore_core.LoreNotFoundError as exc:
        fail(console, str(exc))

    console.print(f"Disabled [bold]{name}[/bold].")
