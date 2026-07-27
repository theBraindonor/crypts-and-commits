from pathlib import Path

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from cac.cli.common import fail
from cac.core import bootstrap as bootstrap_core
from cac.core import world as world_core
from cac.core.git_utils import GitIdentityError

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

    try:
        world_path, world_created = world_core.initialize_world(root)
    except GitIdentityError as exc:
        fail(console, str(exc))
    _report(world_path, world_created)

    mcp_config_path, mcp_config_changed = bootstrap_core.initialize_mcp_config(root)
    _report_mcp_config(mcp_config_path, mcp_config_changed)

    claude_settings_path, claude_settings_changed = bootstrap_core.initialize_claude_settings(root)
    _report_claude_settings(claude_settings_path, claude_settings_changed)

    codex_config_path, codex_config_changed = bootstrap_core.initialize_codex_config(root)
    _report_codex_config(codex_config_path, codex_config_changed)


def _report(path: Path, created: bool) -> None:
    if created:
        console.print(f"Created [bold green]{path}[/bold green]")
    else:
        console.print(f"[bold yellow]{path}[/bold yellow] already exists")


def _report_mcp_config(path: Path, changed: bool) -> None:
    if changed:
        console.print(f"Registered the crypts-and-commits MCP server in [bold green]{path}[/bold green]")
    else:
        console.print(f"[bold yellow]{path}[/bold yellow] already registers the crypts-and-commits MCP server")


def _report_claude_settings(path: Path, changed: bool) -> None:
    if changed:
        console.print(f"Updated permissions in [bold green]{path}[/bold green]")
    else:
        console.print(f"[bold yellow]{path}[/bold yellow] already has the required permissions")


def _report_codex_config(path: Path, changed: bool) -> None:
    if changed:
        console.print(f"Registered the crypts-and-commits MCP server in [bold green]{path}[/bold green]")
    else:
        console.print(f"[bold yellow]{path}[/bold yellow] already registers the crypts-and-commits MCP server")


def _show_splash() -> None:
    title = Text(TITLE, style="bold magenta", justify="center")
    subtitle = Text(SUBTITLE, style="italic cyan", justify="center")
    console.print(Panel(Group(title, subtitle), border_style="magenta", padding=(1, 4)))
