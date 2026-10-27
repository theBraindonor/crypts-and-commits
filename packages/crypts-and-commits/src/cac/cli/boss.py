import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, reference_inputs, resolve_body_input
from cac.core import boss as boss_core
from cac.core import boss_candidates as candidates_core
from cac.core import budget as budget_core
from cac.core import campaign as campaign_core
from cac.core import references
from cac.core.git_utils import GitIdentityError
from cac.core.paths import resolve_project_root

app = typer.Typer(
    help="Capture and manage boss planning records.", context_settings={"help_option_names": ["-h", "--help"]}
)
console = Console()


@app.command("assign-campaign")
@reference_inputs("boss")
def assign_campaign(
    name: str = typer.Argument(..., help="Existing boss name or short reference."),
    campaign_name: str = typer.Argument(..., help="New literal canonical campaign name; never allocated or resolved."),
    body: str | None = typer.Option(
        None, "--body", "-b", help="Tactical campaign Markdown; opens editor if neither body option is supplied."
    ),
    body_file: str | None = typer.Option(None, "--body-file", help="Read UTF-8 campaign body; conflicts with --body."),
) -> None:
    """Create a draft campaign and freeze the eligible boss through reciprocal current links."""
    content = resolve_body_input(body, body_file)
    if content is None:
        content = edit_markdown(campaign_core.template_body())
    result = _call(boss_core.assign_campaign, resolve_project_root(), name, campaign_name, content)
    console.print(references.encoded(result), markup=False, highlight=False, soft_wrap=True)


@app.command("candidates")
@reference_inputs("boss")
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
@reference_inputs("boss")
def get_boss(name: str = typer.Argument(...)) -> None:
    """Show boss metadata, summary, and a budgeted body."""
    root = resolve_project_root()
    metadata, body = _call(boss_core.read_metadata, root, name)
    if "provenance" in metadata:
        body = _call(
            boss_core.budget_response,
            root,
            name,
            {"metadata": metadata, "body": body, "identity": references.Inventory(root).identity("boss", name)},
        )["body"]
    else:
        body = budget_core.truncate_body(
            body, boss_core.boss_path(root, name), budget=references.body_allowance(root, "boss", name)
        )
    for key, value in metadata.items():
        console.print(f"{key}: {value}", markup=False)
    console.print()
    console.print(
        body,
        markup=False,
        soft_wrap=True,
    )


@app.command("list")
@reference_inputs("boss")
def list_bosses(
    cursor: str | None = typer.Option(None, "--cursor"),
    include_archived: bool = typer.Option(False, "--include-archived"),
) -> None:
    """List canonical boss names; ordering does not imply priority."""
    names = _call(boss_core.list_bosses, resolve_project_root(), include_archived=include_archived)
    page_data = _call(references.identity_page, resolve_project_root(), "boss", names, cursor)
    page = budget_core.Page(items=page_data["items"], next_cursor=page_data["next_cursor"])
    console.print(references.encoded({"identities": page_data["identities"]}), markup=False, soft_wrap=True)
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
@reference_inputs("boss", create=True)
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
@reference_inputs("boss")
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


@app.command("record")
@reference_inputs("boss", create=True)
def record_boss(
    name: str = typer.Argument(...),
    progress: str = typer.Option(..., "--progress", help="Reported progress: planned, in_progress, or completed."),
    source: str = typer.Option(..., "--source", help="Roadmap/evidence reference or description."),
    message: str = typer.Option(
        ..., "--message", "-m", help="Recording rationale; describe completion evidence if completed."
    ),
    summary: str = typer.Option(..., "--summary", "-s"),
    completed_on: str | None = typer.Option(
        None, "--completed-on", help="Known historical completion date, YYYY-MM-DD."
    ),
    depends_on: Annotated[
        list[str] | None, typer.Option("--depends-on", help="Existing prerequisite; repeat for each.")
    ] = None,
    body: str | None = typer.Option(None, "--body", "-b"),
    body_file: str | None = typer.Option(None, "--body-file", help="Read UTF-8 Markdown; conflicts with --body."),
) -> None:
    """Capture one existing roadmap goal without inventing campaign history."""
    content = resolve_body_input(body, body_file)
    if content is None:
        content = edit_markdown(boss_core.template_body())
    path = _call(
        boss_core.record_boss,
        resolve_project_root(),
        name,
        content,
        summary,
        progress,
        source,
        message,
        completed_on,
        depends_on,
    )
    console.print(str(path), markup=False)


@app.command("make-available")
@reference_inputs("boss")
def make_available(name: str = typer.Argument(...)) -> None:
    """Mark an unassigned proposed boss available, regardless of prerequisites."""
    path: Path = _call(boss_core.make_available, resolve_project_root(), name)
    console.print(str(path), markup=False)


@app.command("withdraw")
@reference_inputs("boss")
def withdraw(name: str = typer.Argument(...)) -> None:
    """Withdraw an unassigned proposed or available boss."""
    path: Path = _call(boss_core.withdraw, resolve_project_root(), name)
    console.print(str(path), markup=False)


@app.command("reactivate")
@reference_inputs("boss")
def reactivate(name: str = typer.Argument(...)) -> None:
    """Return an unarchived, unassigned withdrawn boss to proposed."""
    path: Path = _call(boss_core.reactivate, resolve_project_root(), name)
    console.print(str(path), markup=False)


@app.command("archive")
@reference_inputs("boss")
def archive_boss(name: str = typer.Argument(...)) -> None:
    """Archive an unassigned withdrawn or externally recorded completed boss."""
    path: Path = _call(boss_core.archive_boss, resolve_project_root(), name)
    console.print(str(path), markup=False)


@app.command("assign-dependency")
@reference_inputs("boss")
def assign_dependency(name: str = typer.Argument(...), dependency: str = typer.Argument(...)) -> None:
    """Assign a direct canonical prerequisite; validate the resulting graph."""
    path = _call(boss_core.assign_dependency, resolve_project_root(), name, dependency)
    console.print(str(path), markup=False)


@app.command("unassign-dependency")
@reference_inputs("boss", remove=True)
def unassign_dependency(name: str = typer.Argument(...), dependency: str = typer.Argument(...)) -> None:
    """Unassign a direct canonical prerequisite; validate the resulting graph."""
    path = _call(boss_core.unassign_dependency, resolve_project_root(), name, dependency)
    console.print(str(path), markup=False)
