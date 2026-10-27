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
    """Read freshness and indexed snapshot counts. Missing/stale indexes require developer-run
    cac index rebuild; reads never rebuild or migrate the cache."""
    return search_index_core.status(resolve_project_root())


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
    Boss summary/body is searchable. Archives are excluded unless requested. Missing indexes
    return built=false; stale indexes return stale=true with no hits and a recovery diagnostic.
    Rebuild is developer-only via cac index rebuild, never automatic or exposed over MCP."""
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
    except search_index_core.StaleIndexError as exc:
        return search_index_core.bounded_response(
            {"built": True, "stale": True, "hits": [], "diagnostic": exc.diagnostic}
        )
    if hits is None:
        return search_index_core.bounded_response({"built": False, "stale": False, "hits": []})
    return search_index_core.bounded_response(
        {"built": True, "stale": False, "hits": [_hit_to_dict(hit) for hit in hits]}
    )
