from dataclasses import asdict
from pathlib import Path

from cac.core import search_index as search_index_core
from langchain_core.tools import BaseTool, tool


def build_tools(root: Path) -> list[BaseTool]:
    def search_sourcebook(
        phrase: str, object_type: str | None = None, limit: int = 10, include_archived: bool = False
    ) -> dict:
        """Full-text search the sourcebook index for phrase, ranked by relevance. object_type
        optionally filters to one of: encounter, campaign, lore, region, world. Returns
        {"available": False, "hits": []} if the search index hasn't been built yet - that is
        distinct from a built index returning zero matches, so treat "available": False as
        "search isn't ready" rather than "no results"."""
        hits = search_index_core.search(
            root, phrase, object_type=object_type, limit=limit, include_archived=include_archived
        )
        if hits is None:
            return {"available": False, "hits": []}
        return {"available": True, "hits": [asdict(hit) for hit in hits]}

    return [tool(search_sourcebook)]
