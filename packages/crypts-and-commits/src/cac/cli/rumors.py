from collections.abc import Callable
from typing import Any

import typer
from rich.console import Console

from cac.cli.common import edit_markdown, resolve_body_input
from cac.core import references, rumors
from cac.core.paths import resolve_project_root

app = typer.Typer(help="Manage freeform campaign rumors.", context_settings={"help_option_names": ["-h", "--help"]})
console = Console()


def _call(operation: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    try:
        return operation(*args, **kwargs)
    except (ValueError, OSError) as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(1) from exc


def _print(result: dict[str, Any]) -> None:
    console.print(references.encoded(result), markup=False, highlight=False, soft_wrap=True)


@app.command("list")
def list_documents(cursor: str | None = typer.Option(None, "--cursor")) -> None:
    """Page all existing documents, including archived campaign owners."""
    _print(_call(rumors.list_documents, resolve_project_root(), cursor))


@app.command("get")
def get(
    campaign: str | None = typer.Option(None, "--campaign", "-c"),
    cursor: str | None = typer.Option(None, "--cursor"),
) -> None:
    """Return JSON with literal body and next_cursor for continuation; omitted campaign uses active fallback."""
    _print(_call(rumors.get, resolve_project_root(), campaign, cursor))


def _write(campaign: str | None, body: str | None, body_file: str | None, *, update: bool) -> None:
    content = resolve_body_input(body, body_file)
    root = resolve_project_root()
    if content is None:
        initial = _call(rumors.read_body, root, campaign) if update else ""
        content = edit_markdown(initial)
    _print(_call(rumors.write, root, content, campaign, update=update))


@app.command("create")
def create(
    campaign: str | None = typer.Option(None, "--campaign", "-c"),
    body: str | None = typer.Option(None, "--body", "-b"),
    body_file: str | None = typer.Option(None, "--body-file"),
) -> None:
    """Create rumors using inline text, a UTF-8 file, or the editor."""
    _write(campaign, body, body_file, update=False)


@app.command("update")
def update(
    campaign: str | None = typer.Option(None, "--campaign", "-c"),
    body: str | None = typer.Option(None, "--body", "-b"),
    body_file: str | None = typer.Option(None, "--body-file"),
) -> None:
    """Replace rumors using inline text, a UTF-8 file, or the editor."""
    _write(campaign, body, body_file, update=True)


@app.command("delete")
def delete(
    campaign: str | None = typer.Option(None, "--campaign", "-c"),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Delete a document after confirmation, or use --yes."""
    if not yes:
        typer.confirm("Delete campaign rumors?", abort=True)
    _print(_call(rumors.delete, resolve_project_root(), campaign))
