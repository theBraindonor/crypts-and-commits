import typer
from rich.console import Console

from cac.cli.common import fail
from cac.core import budget as budget_core
from cac.core import docs as docs_core
from cac.core.config import DOCS_RESPONSE_BUDGET

app = typer.Typer(
    help=(
        "Read the framework's packaged reference docs - guide documents shipped with cac "
        "(e.g. the Workflow Reference Guide), distinct from .sourcebook content. Read-only."
    )
)
console = Console()


@app.command("list")
def list_docs(
    cursor: str | None = typer.Option(None, "--cursor", help="Resume from a previous page's cursor."),
) -> None:
    """List registered docs as name + summary pairs, paged under the response budget."""
    items = [{"name": name, "summary": summary} for name, summary in docs_core.list_docs()]
    if not items:
        console.print("No docs registered.")
        return

    try:
        page = budget_core.paginate(items, cursor, render=lambda item: item["name"] + item["summary"])
    except budget_core.InvalidCursorError as exc:
        fail(console, str(exc))

    for item in page.items:
        console.print(f"[bold]{item['name']}[/bold]: ", end="")
        console.print(item["summary"], markup=False)
    if page.next_cursor is not None:
        console.print(f"[dim]More results - pass --cursor {page.next_cursor} to continue.[/dim]")


@app.command("get")
def get_doc(
    name: str = typer.Argument(..., help="Doc name to show."),
) -> None:
    """Show a registered doc's full body."""
    try:
        body = docs_core.read_doc(name)
    except docs_core.DocNotFoundError as exc:
        fail(console, str(exc))

    body = budget_core.truncate_body(body, docs_core.doc_source_path(name), budget=DOCS_RESPONSE_BUDGET)
    console.print(body, markup=False, soft_wrap=True)
