from typing import Any

from cac.core import search_index as search_index_core
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp


def _hit_to_dict(hit: search_index_core.SearchHit) -> dict[str, Any]:
    return {
        "rank": hit.rank,
        "score": hit.score,
        "object_type": hit.object_type,
        "campaign": hit.campaign,
        "name": hit.name,
        "status": hit.status,
        "updated_on": hit.updated_on,
        "archived": hit.archived,
        "excerpt": hit.excerpt,
    }


@mcp.tool()
def index_status() -> dict[str, Any]:
    """Show how many items are indexed, by object type. `built` is False if the index has never
    been built - run `index_rebuild` via the `cac` CLI to build one (index rebuild is
    developer-only and not exposed over MCP)."""
    counts = search_index_core.index_counts(resolve_project_root())
    if counts is None:
        return {"built": False, "counts": {}}
    return {"built": True, "counts": counts}


@mcp.tool()
def index_search(
    phrase: str,
    max_results: int = search_index_core.SEARCH_DEFAULT_MAX_RESULTS,
    skip: int = 0,
    object_type: str | None = None,
    snippet_tokens: int = search_index_core.SEARCH_DEFAULT_SNIPPET_TOKENS,
    include_archived: bool = False,
) -> dict[str, Any]:
    """Search the index for a phrase, ranked by relevance, with a matching excerpt per result.
    Archived campaigns/encounters are excluded by default - pass include_archived=True to include
    them. `built` is False if the index has never been built - run `index_rebuild` via the `cac`
    CLI to build one (index rebuild is developer-only and not exposed over MCP)."""
    hits = search_index_core.search(
        resolve_project_root(),
        phrase,
        object_type=object_type,
        limit=max_results,
        offset=skip,
        snippet_tokens=snippet_tokens,
        include_archived=include_archived,
    )
    if hits is None:
        return {"built": False, "hits": []}
    return {"built": True, "hits": [_hit_to_dict(hit) for hit in hits]}
