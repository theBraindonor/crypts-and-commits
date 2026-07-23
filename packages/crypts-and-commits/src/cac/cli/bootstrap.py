from pathlib import Path

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from cac.core import bootstrap as bootstrap_core
from cac.core import world as world_core

TITLE = "Crypts And Commits"
SUBTITLE = "A Code Assistant Continuity Framework"

app = typer.Typer(help="Bootstrap a repository for Crypts and Commits.")
console = Console()


@app.command()
def init() -> None:
    """Create the .sourcebook directory and world file in the current repository."""
    _show_splash()
    root = Path.cwd()

    sourcebook_dir, sourcebook_created = bootstrap_core.initialize(root)
    _report(sourcebook_dir, sourcebook_created)

    world_path, world_created = world_core.initialize_world(root)
    _report(world_path, world_created)


def _report(path: Path, created: bool) -> None:
    if created:
        console.print(f"Created [bold green]{path}[/bold green]")
    else:
        console.print(f"[bold yellow]{path}[/bold yellow] already exists")


def _show_splash() -> None:
    title = Text(TITLE, style="bold magenta", justify="center")
    subtitle = Text(SUBTITLE, style="italic cyan", justify="center")
    console.print(Panel(Group(title, subtitle), border_style="magenta", padding=(1, 4)))
