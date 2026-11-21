from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console

from cac.cli.common import CURSOR_HELP, edit_markdown, print_body, reference_inputs, resolve_body_input
from cac.core import references
from cac.core import ruling as ruling_core
from cac.core.git_utils import GitIdentityError
from cac.core.paths import resolve_project_root

app = typer.Typer(
    help="Record developer rulings made during a campaign and triage them on planning.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()

_NAME_HELP = "Canonical ruling name, cNNN-eNNN-slug; rulings have no short references."


def _call(operation: Callable, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except (ValueError, OSError, GitIdentityError) as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(code=1) from exc


@app.command("list")
@reference_inputs("ruling")
def list_rulings(
    cursor: str | None = typer.Option(None, "--cursor"),
    include_archived: bool = typer.Option(False, "--include-archived"),
    status: str | None = typer.Option(
        None, "--status", help="Only rulings with this status: recorded, canonized, noted."
    ),
) -> None:
    """List canonical ruling names, optionally filtered by status."""
    root = resolve_project_root()
    names = _call(ruling_core.list_rulings, root, include_archived=include_archived, status=status)
    page = _call(references.identity_page, root, "ruling", names, cursor)
    console.print(references.encoded({"identities": page["identities"]}), markup=False, soft_wrap=True)
    for name in page["items"]:
        console.print(name, markup=False)
    if page["next_cursor"] is not None:
        console.print(f"Next cursor: {page['next_cursor']}", markup=False)


@app.command("get")
@reference_inputs("ruling")
def get_ruling(
    name: str = typer.Argument(..., help=_NAME_HELP),
    cursor: str | None = typer.Option(None, "--cursor", help=CURSOR_HELP),
) -> None:
    """Show ruling metadata, summary, and a budgeted body; long bodies continue with --cursor."""
    root = resolve_project_root()
    payload = _call(ruling_core.get_payload, root, name)
    response = _call(references.get_response, root, "ruling", payload, name, cursor)
    for key, value in response["metadata"].items():
        console.print(f"{key}: {value}", markup=False)
    console.print(f"summary: {response['summary']}", markup=False)
    console.print()
    print_body(console, response)


def _body_write(name: str, body: str | None, body_file: str | None, summary: str, origin: str, *, update: bool) -> None:
    root = resolve_project_root()
    content = resolve_body_input(body, body_file)
    if content is None:
        initial = _call(ruling_core.read_metadata, root, name)[1] if update else ruling_core.template_body()
        content = edit_markdown(initial)
    operation = ruling_core.update_ruling if update else ruling_core.create_ruling
    path = _call(operation, root, name, content, summary, origin)
    console.print(str(path), markup=False)


@app.command("create")
@reference_inputs("ruling", create=True)
def create_ruling(
    name: str = typer.Argument(
        ..., help="New literal cNNN-eNNN-slug name (e000 for no encounter); the campaign must be open."
    ),
    body: str | None = typer.Option(
        None, "--body", "-b", help="Markdown body; opens editor if neither body option is supplied."
    ),
    body_file: str | None = typer.Option(
        None, "--body-file", help="Read Markdown from a UTF-8 file; conflicts with --body."
    ),
    summary: str = typer.Option(..., "--summary", "-s"),
    origin: str = typer.Option(..., "--origin", "-o", help="Who made or prompted the decision, in any words."),
) -> None:
    """Record a ruling made during the open campaign named by its cNNN prefix."""
    _body_write(name, body, body_file, summary, origin, update=False)


@app.command("update")
@reference_inputs("ruling")
def update_ruling(
    name: str = typer.Argument(..., help=_NAME_HELP),
    body: str | None = typer.Option(
        None, "--body", "-b", help="Markdown body; opens editor if neither body option is supplied."
    ),
    body_file: str | None = typer.Option(
        None, "--body-file", help="Read Markdown from a UTF-8 file; conflicts with --body."
    ),
    summary: str = typer.Option(..., "--summary", "-s"),
    origin: str = typer.Option(..., "--origin", "-o", help="Who made or prompted the decision, in any words."),
) -> None:
    """Replace a recorded ruling's body, summary, and origin together."""
    _body_write(name, body, body_file, summary, origin, update=True)


@app.command("canonize")
@reference_inputs("ruling")
def canonize(
    name: str = typer.Argument(..., help=_NAME_HELP),
    message: str = typer.Option(..., "--message", "-m", help="Required narrative of how the world was updated."),
) -> None:
    """Mark a recorded ruling canonized, with a narrative of the lore/region/world updates made."""
    path: Path = _call(ruling_core.canonize, resolve_project_root(), name, message)
    console.print(str(path), markup=False)


@app.command("note")
@reference_inputs("ruling")
def note(
    name: str = typer.Argument(..., help=_NAME_HELP),
    message: str = typer.Option(..., "--message", "-m", help="Required narrative of why no world update is needed."),
) -> None:
    """Mark a recorded ruling noted, with a narrative of why it needs no world update."""
    path: Path = _call(ruling_core.note, resolve_project_root(), name, message)
    console.print(str(path), markup=False)


@app.command("reopen")
@reference_inputs("ruling")
def reopen(
    name: str = typer.Argument(..., help=_NAME_HELP),
    message: str = typer.Option(..., "--message", "-m", help="Required reason for reopening."),
) -> None:
    """Return an unarchived canonized or noted ruling to recorded, clearing its resolution."""
    path: Path = _call(ruling_core.reopen, resolve_project_root(), name, message)
    console.print(str(path), markup=False)


@app.command("archive")
@reference_inputs("ruling")
def archive_ruling(name: str = typer.Argument(..., help=_NAME_HELP)) -> None:
    """Archive a canonized or noted ruling; its name stays reserved and readable."""
    path: Path = _call(ruling_core.archive_ruling, resolve_project_root(), name)
    console.print(str(path), markup=False)
