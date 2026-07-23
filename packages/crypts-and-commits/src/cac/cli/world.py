from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, fail
from cac.core import world as world_core

app = typer.Typer(
    help=(
        "View and edit the project's world file. The world file holds summary details of the "
        "project - a description of its goals and/or purpose. It is intended for use when "
        "generating context, prior to including the world-level lore items. World-level lore "
        "items are used to review all encounters before they are opened."
    )
)
console = Console()


@app.command("get")
def get_world() -> None:
    """Show the world file's frontmatter and body."""
    try:
        world = world_core.read_world(Path.cwd())
    except world_core.WorldNotFoundError as exc:
        fail(console, str(exc))

    for key, value in world.metadata.items():
        console.print(f"[bold]{key}[/bold]: {value}")
    console.print()
    console.print(world.body, markup=False)


@app.command("set")
def set_attribute(
    key: str = typer.Argument(..., help="Frontmatter attribute name."),
    value: str = typer.Argument(..., help="Frontmatter attribute value."),
) -> None:
    """Set a frontmatter attribute on the world file."""
    try:
        world_core.set_attribute(Path.cwd(), key, value)
    except world_core.WorldNotFoundError as exc:
        fail(console, str(exc))

    console.print(f"Set [bold]{key}[/bold] = {value}")


@app.command("set-body")
def set_body(
    body: str | None = typer.Option(None, "--body", "-b", help="Markdown body. Opens an editor if omitted."),
) -> None:
    """Update the world file's body."""
    try:
        current = world_core.read_world(Path.cwd())
    except world_core.WorldNotFoundError as exc:
        fail(console, str(exc))

    content = body if body is not None else edit_markdown(current.body)
    world_core.update_body(Path.cwd(), content)
    console.print("Updated world body.")
