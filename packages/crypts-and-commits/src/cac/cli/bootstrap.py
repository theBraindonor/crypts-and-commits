from pathlib import Path

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from cac.core import bootstrap as bootstrap_core

TITLE = "Crypts And Commits"
SUBTITLE = "A Code Assistant Continuity Framework"

app = typer.Typer(help="Bootstrap a repository for Crypts and Commits.")
console = Console()


@app.command()
def init() -> None:
    """Create the .sourcebook directory in the current repository."""
    _show_splash()
    sourcebook_dir, created = bootstrap_core.initialize(Path.cwd())
    if created:
        console.print(f"Created [bold green]{sourcebook_dir}[/bold green]")
    else:
        console.print(f"[bold yellow]{sourcebook_dir}[/bold yellow] already exists")


def _show_splash() -> None:
    title = Text(TITLE, style="bold magenta", justify="center")
    subtitle = Text(SUBTITLE, style="italic cyan", justify="center")
    console.print(Panel(Group(title, subtitle), border_style="magenta", padding=(1, 4)))
