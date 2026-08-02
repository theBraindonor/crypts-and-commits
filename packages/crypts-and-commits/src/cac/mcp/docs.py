from typing import Any

from cac.core import budget as budget_core
from cac.core import docs as docs_core
from cac.core.config import DOCS_RESPONSE_BUDGET
from cac.mcp.instance import mcp


@mcp.tool()
def docs_list(cursor: str | None = None) -> dict[str, Any]:
    """List registered reference docs as name + summary pairs, paged under the response budget.
    Docs are framework-owned guide documents (e.g. the Workflow Reference Guide) - read-only,
    distinct from .sourcebook content. summary is a routing signal; hydrate with docs_get(name)
    for the full body."""
    items = [{"name": name, "summary": summary} for name, summary in docs_core.list_docs()]
    page = budget_core.paginate(items, cursor, render=lambda item: item["name"] + item["summary"])
    return {"items": page.items, "next_cursor": page.next_cursor}


@mcp.tool()
def docs_get(name: str) -> dict[str, Any]:
    """Show a registered doc's full body - e.g. docs_get("workflow") for the Workflow Reference
    Guide. Body is truncated under a dedicated, larger docs response budget (docs are a small
    curated set meant to be read whole, not unbounded .sourcebook content); read the file
    directly at the reported path if truncated."""
    summary = docs_core.doc_summary(name)
    body = docs_core.read_doc(name)
    body = budget_core.truncate_body(body, docs_core.doc_source_path(name), budget=DOCS_RESPONSE_BUDGET)
    return {"name": name, "summary": summary, "body": body}
