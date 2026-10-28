from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import CURSOR_HELP, edit_markdown, print_body, reference_inputs, resolve_body_input
from cac.core import references
from cac.core import rumor as rumor_core
from cac.core.git_utils import GitIdentityError
from cac.core.paths import resolve_project_root

app = typer.Typer(
    help="Capture and triage standalone backlog rumors.", context_settings={"help_option_names": ["-h", "--help"]}
)
console = Console()


def _call(operation: Callable, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except (ValueError, OSError, GitIdentityError) as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(code=1) from exc


@app.command("list")
@reference_inputs("rumor")
def list_rumors(
    cursor: str | None = typer.Option(None, "--cursor"),
    include_archived: bool = typer.Option(False, "--include-archived"),
    status: str | None = typer.Option(
        None, "--status", help="Only rumors with this status: open, promoted, dismissed."
    ),
) -> None:
    """List canonical rumor names, optionally filtered by status; ordering does not imply priority."""
    root = resolve_project_root()
    names = _call(rumor_core.list_rumors, root, include_archived=include_archived, status=status)
    page = _call(references.identity_page, root, "rumor", names, cursor)
    console.print(references.encoded({"identities": page["identities"]}), markup=False, soft_wrap=True)
    for name in page["items"]:
        console.print(name, markup=False)
    if page["next_cursor"] is not None:
        console.print(f"Next cursor: {page['next_cursor']}", markup=False)


@app.command("get")
@reference_inputs("rumor")
def get_rumor(
    name: str = typer.Argument(...),
    cursor: str | None = typer.Option(None, "--cursor", help=CURSOR_HELP),
) -> None:
    """Show rumor metadata, summary, and a budgeted body; long bodies continue with --cursor."""
    root = resolve_project_root()
    payload = _call(rumor_core.get_payload, root, name)
    response = _call(references.get_response, root, "rumor", payload, name, cursor)
    for key, value in response["metadata"].items():
        console.print(f"{key}: {value}", markup=False)
    console.print(f"summary: {response['summary']}", markup=False)
    console.print()
    print_body(console, response)


def _body_write(name: str, body: str | None, body_file: str | None, summary: str, origin: str, *, update: bool) -> None:
    root = resolve_project_root()
    content = resolve_body_input(body, body_file)
    if content is None:
        initial = _call(rumor_core.read_metadata, root, name)[1] if update else rumor_core.template_body()
        content = edit_markdown(initial)
    operation = rumor_core.update_rumor if update else rumor_core.create_rumor
    path = _call(operation, root, name, content, summary, origin)
    console.print(str(path), markup=False)


@app.command("create")
@reference_inputs("rumor", create=True)
def create_rumor(
    name: str = typer.Argument(..., help="New literal canonical rumor name; never allocated or resolved."),
    body: str | None = typer.Option(
        None, "--body", "-b", help="Markdown body; opens editor if neither body option is supplied."
    ),
    body_file: str | None = typer.Option(
        None, "--body-file", help="Read Markdown from a UTF-8 file; conflicts with --body."
    ),
    summary: str = typer.Option(..., "--summary", "-s"),
    origin: str = typer.Option(..., "--origin", "-o", help="Who or what raised the rumor, in any words."),
) -> None:
    """Create an open rumor with body, routing summary, and free-text origin."""
    _body_write(name, body, body_file, summary, origin, update=False)


@app.command("update")
@reference_inputs("rumor")
def update_rumor(
    name: str = typer.Argument(...),
    body: str | None = typer.Option(
        None, "--body", "-b", help="Markdown body; opens editor if neither body option is supplied."
    ),
    body_file: str | None = typer.Option(
        None, "--body-file", help="Read Markdown from a UTF-8 file; conflicts with --body."
    ),
    summary: str = typer.Option(..., "--summary", "-s"),
    origin: str = typer.Option(..., "--origin", "-o", help="Who or what raised the rumor, in any words."),
) -> None:
    """Replace an open rumor's body, summary, and origin together."""
    _body_write(name, body, body_file, summary, origin, update=True)


@app.command("promote")
@reference_inputs("rumor")
def promote(
    name: str = typer.Argument(...),
    boss: str = typer.Argument(..., help="Existing unassigned proposed/available boss name or short reference."),
    message: str | None = typer.Option(None, "--message", "-m", help="Optional promotion note."),
) -> None:
    """Link an open rumor to an existing unassigned boss; the boss record is never written."""
    path: Path = _call(rumor_core.promote, resolve_project_root(), name, boss, message)
    console.print(str(path), markup=False)


@app.command("dismiss")
@reference_inputs("rumor")
def dismiss(
    name: str = typer.Argument(...),
    message: str = typer.Option(..., "--message", "-m", help="Required dismissal reason."),
) -> None:
    """Dismiss an open rumor with a required reason."""
    path: Path = _call(rumor_core.dismiss, resolve_project_root(), name, message)
    console.print(str(path), markup=False)


@app.command("reopen")
@reference_inputs("rumor")
def reopen(
    name: str = typer.Argument(...),
    message: str = typer.Option(..., "--message", "-m", help="Required reason for reopening."),
) -> None:
    """Return an unarchived promoted or dismissed rumor to open, clearing its boss link."""
    path: Path = _call(rumor_core.reopen, resolve_project_root(), name, message)
    console.print(str(path), markup=False)


@app.command("archive")
@reference_inputs("rumor")
def archive_rumor(name: str = typer.Argument(...)) -> None:
    """Archive a promoted or dismissed rumor; its name stays reserved and readable."""
    path: Path = _call(rumor_core.archive_rumor, resolve_project_root(), name)
    console.print(str(path), markup=False)


@app.command("renumber")
@reference_inputs("rumor")
def renumber(
    name: str = typer.Argument(...),
    new_name: str = typer.Argument(..., help="New unused literal canonical name; never allocated or resolved."),
) -> None:
    """Rename a live open or dismissed rumor; promoted rumors keep their number."""
    path: Path = _call(rumor_core.renumber, resolve_project_root(), name, new_name)
    console.print(str(path), markup=False)
