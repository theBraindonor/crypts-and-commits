import typer
from rich.console import Console

from cac.core import search_index as search_index_core
from cac.core.paths import resolve_project_root

app = typer.Typer(
    help=(
        "Build and inspect the search index over .sourcebook content. The index stays in sync "
        "automatically as content is created, updated, or deleted through cac - 'rebuild' is only "
        "needed for the first build, or to catch up on changes made outside cac (e.g. a git pull)."
    )
)
console = Console()


@app.command("status")
def status() -> None:
    """Show index freshness and snapshot counts by type."""
    try:
        result = search_index_core.status(resolve_project_root())
    except ValueError as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(1) from exc
    counts = result["counts"]
    if not result["built"]:
        console.print("No index has been built yet. Run [bold]cac index rebuild[/bold] to build one.")
        return
    console.print("Freshness: " + result["freshness"], markup=False)
    if result["freshness"] == "stale":
        console.print("Counts describe the indexed snapshot. " + result["diagnostic"]["message"], markup=False)
        console.print(result["diagnostic"]["recovery"], markup=False)
    total = sum(counts.values())
    console.print(f"[bold]{total}[/bold] item(s) indexed.")
    for object_type, count in sorted(counts.items()):
        console.print(f"  {object_type}: {count}", markup=False)


@app.command("rebuild")
def rebuild() -> None:
    """Fully rebuild the index from .sourcebook content on disk."""
    count = search_index_core.rebuild_index(resolve_project_root())
    console.print(f"Rebuilt index: [bold]{count}[/bold] item(s) indexed.")


@app.command("search")
def search(
    phrase: str = typer.Argument(..., help="Phrase to search for."),
    max_results: int = typer.Option(
        search_index_core.SEARCH_DEFAULT_MAX_RESULTS, "--max-results", "-n", help="Maximum number of results."
    ),
    skip: int = typer.Option(0, "--skip", "-s", help="Number of top results to skip, for paging."),
    object_type: str | None = typer.Option(
        None, "--type", "-t", help="Restrict to one document type. Defaults to all types."
    ),
    snippet_tokens: int = typer.Option(
        search_index_core.SEARCH_DEFAULT_SNIPPET_TOKENS,
        "--snippet-tokens",
        help="Snippet excerpt length, in tokens (1-64).",
    ),
    include_archived: bool = typer.Option(
        False, "--include-archived", help="Also include archived campaigns/encounters/bosses, excluded by default."
    ),
) -> None:
    """Search the index for a phrase, ranked by relevance, with a matching excerpt per result.
    Archives are excluded by default. Stale snapshots report an error without hits."""
    try:
        hits = search_index_core.search(
            resolve_project_root(),
            phrase,
            object_type=object_type,
            limit=max_results,
            offset=skip,
            snippet_tokens=snippet_tokens,
            include_archived=include_archived,
        )
    except (
        search_index_core.EmptySearchPhraseError,
        search_index_core.InvalidSearchQueryError,
        search_index_core.StaleIndexError,
    ) as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(1) from exc

    if hits is None:
        console.print("No index has been built yet. Run [bold]cac index rebuild[/bold] to build one.")
        return
    if not hits:
        console.print(f"No results for {phrase!r}.", markup=False)
        return

    console.print("[dim]RANK  SCORE   TYPE        NAME  STATUS  UPDATED[/dim]")
    console.print()
    for hit in hits:
        archived_suffix = " (archived)" if hit.archived else ""
        console.print(
            f"#{hit.rank}  {hit.score:.3f}  [{hit.object_type}] {hit.name}  [{hit.status}]{archived_suffix}  "
            f"updated {hit.updated_on}",
            markup=False,
        )
        console.print(f"    {hit.excerpt}", markup=False)

    if len(hits) == max_results:
        console.print(f"[dim]More results may exist - pass --skip {skip + max_results} to continue.[/dim]")
