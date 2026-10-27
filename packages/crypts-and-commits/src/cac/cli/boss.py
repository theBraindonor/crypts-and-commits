import json
from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, resolve_body_input
from cac.core import boss as boss_core
from cac.core import boss_candidates as candidates_core
from cac.core import budget as budget_core
from cac.core.git_utils import GitIdentityError
from cac.core.paths import resolve_project_root

app = typer.Typer(
    help="Capture and manage boss planning records.", context_settings={"help_option_names": ["-h", "--help"]}
)
console = Console()


@app.command("candidates")
def candidates(
    cursor: str | None = typer.Option(None, "--cursor", help="Resume candidate discovery from a previous page."),
) -> None:
    """Show bounded JSON summaries, eligibility, blockers, counts, and diagnostics from local records."""
    result = _call(candidates_core.candidates, resolve_project_root(), cursor)
    console.print(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")), markup=False, soft_wrap=True, highlight=False
    )


def _call(operation: Callable, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except (ValueError, OSError, GitIdentityError) as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(code=1) from exc


@app.command("get")
def get_boss(name: str = typer.Argument(...)) -> None:
    """Show boss metadata, summary, and a budgeted body."""
    root = resolve_project_root()
    metadata, body = _call(boss_core.read_metadata, root, name)
    for key, value in metadata.items():
        console.print(f"{key}: {value}", markup=False)
    console.print()
    console.print(budget_core.truncate_body(body, boss_core.boss_path(root, name)), markup=False, soft_wrap=True)


@app.command("list")
def list_bosses(
    cursor: str | None = typer.Option(None, "--cursor"),
    include_archived: bool = typer.Option(False, "--include-archived"),
) -> None:
    """List canonical boss names; ordering does not imply priority."""
    names = _call(boss_core.list_bosses, resolve_project_root(), include_archived=include_archived)
    page = _call(budget_core.paginate, names, cursor)
    for name in page.items:
        console.print(name, markup=False)
    if page.next_cursor is not None:
        console.print(f"Next cursor: {page.next_cursor}", markup=False)


def _body_write(name: str, body: str | None, body_file: str | None, summary: str, *, update: bool) -> None:
    root = resolve_project_root()
    content = resolve_body_input(body, body_file)
    if content is None:
        initial = _call(boss_core.read_metadata, root, name)[1] if update else boss_core.template_body()
        content = edit_markdown(initial)
    operation = boss_core.update_boss if update else boss_core.create_boss
    path = _call(operation, root, name, content, summary)
    console.print(str(path), markup=False)


@app.command("create")
def create_boss(
    name: str = typer.Argument(...),
    body: str | None = typer.Option(
        None, "--body", "-b", help="Markdown body; opens editor if neither body option is supplied."
    ),
    body_file: str | None = typer.Option(
        None, "--body-file", help="Read Markdown from a UTF-8 file; conflicts with --body."
    ),
    summary: str = typer.Option(..., "--summary", "-s"),
) -> None:
    """Create a proposed boss with body and routing summary."""
    _body_write(name, body, body_file, summary, update=False)


@app.command("update")
def update_boss(
    name: str = typer.Argument(...),
    body: str | None = typer.Option(
        None, "--body", "-b", help="Markdown body; opens editor if neither body option is supplied."
    ),
    body_file: str | None = typer.Option(
        None, "--body-file", help="Read Markdown from a UTF-8 file; conflicts with --body."
    ),
    summary: str = typer.Option(..., "--summary", "-s"),
) -> None:
    """Replace editable planning body and summary together."""
    _body_write(name, body, body_file, summary, update=True)


@app.command("make-available")
def make_available(name: str = typer.Argument(...)) -> None:
    """Mark an unassigned proposed boss available, regardless of prerequisites."""
    path: Path = _call(boss_core.make_available, resolve_project_root(), name)
    console.print(str(path), markup=False)


@app.command("withdraw")
def withdraw(name: str = typer.Argument(...)) -> None:
    """Withdraw an unassigned proposed or available boss."""
    path: Path = _call(boss_core.withdraw, resolve_project_root(), name)
    console.print(str(path), markup=False)


@app.command("reactivate")
def reactivate(name: str = typer.Argument(...)) -> None:
    """Return an unarchived, unassigned withdrawn boss to proposed."""
    path: Path = _call(boss_core.reactivate, resolve_project_root(), name)
    console.print(str(path), markup=False)


@app.command("archive")
def archive_boss(name: str = typer.Argument(...)) -> None:
    """Archive an unassigned withdrawn boss, retaining its name and status."""
    path: Path = _call(boss_core.archive_boss, resolve_project_root(), name)
    console.print(str(path), markup=False)


@app.command("assign-dependency")
def assign_dependency(name: str = typer.Argument(...), dependency: str = typer.Argument(...)) -> None:
    """Assign a direct canonical prerequisite; validate the resulting graph."""
    path = _call(boss_core.assign_dependency, resolve_project_root(), name, dependency)
    console.print(str(path), markup=False)


@app.command("unassign-dependency")
def unassign_dependency(name: str = typer.Argument(...), dependency: str = typer.Argument(...)) -> None:
    """Unassign a direct canonical prerequisite; validate the resulting graph."""
    path = _call(boss_core.unassign_dependency, resolve_project_root(), name, dependency)
    console.print(str(path), markup=False)
