import typer
from rich.console import Console

from cac.cli.common import CURSOR_HELP, edit_markdown, fail, fitted, print_body, resolve_body_input
from cac.core import budget as budget_core
from cac.core import world as world_core
from cac.core.git_utils import GitIdentityError
from cac.core.paths import resolve_project_root

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
def get_world(cursor: str | None = typer.Option(None, "--cursor", help=CURSOR_HELP)) -> None:
    """Show the world file's frontmatter and body; long bodies continue with --cursor."""
    try:
        payload = world_core.get_payload(resolve_project_root())
    except world_core.WorldNotFoundError as exc:
        fail(console, str(exc))
    response = fitted(console, lambda: budget_core.fit_response(payload, cursor, "world_get"))

    for key, value in response["metadata"].items():
        console.print(f"{key}:", style="bold", markup=False, end=" ")
        console.print(value, markup=False)
    console.print()
    print_body(console, response)


@app.command("set")
def set_attribute(
    key: str = typer.Argument(..., help="Frontmatter attribute name, such as merge_target_branch or planning_branch."),
    value: str = typer.Argument(..., help="Frontmatter attribute value."),
) -> None:
    """Set a frontmatter attribute on the world file."""
    try:
        world_core.set_attribute(resolve_project_root(), key, value)
    except (world_core.WorldNotFoundError, GitIdentityError) as exc:
        fail(console, str(exc))

    console.print("Set", end=" ")
    console.print(key, style="bold", markup=False, end=" = ")
    console.print(value, markup=False)


@app.command("set-body")
def set_body(
    body: str | None = typer.Option(
        None, "--body", "-b", help="Markdown body. Opens an editor if neither body option is supplied."
    ),
    body_file: str | None = typer.Option(
        None, "--body-file", metavar="PATH", help="UTF-8 body file; cannot be combined with --body/-b."
    ),
) -> None:
    """Update the world file's body."""
    try:
        current = world_core.read_world(resolve_project_root())
    except world_core.WorldNotFoundError as exc:
        fail(console, str(exc))

    body = resolve_body_input(body, body_file)
    content = body if body is not None else edit_markdown(current.body)
    try:
        world_core.update_body(resolve_project_root(), content)
    except GitIdentityError as exc:
        fail(console, str(exc))
    console.print("Updated world body.")
