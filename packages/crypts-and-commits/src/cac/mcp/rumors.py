from typing import Any

from cac.core import rumors
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp


@mcp.tool()
def rumors_list(cursor: str | None = None) -> dict[str, Any]:
    """Page existing rumors across all campaign owners, including archived owners and orphan diagnostics."""
    return rumors.list_documents(resolve_project_root(), cursor)


@mcp.tool()
def rumors_get(campaign: str | None = None, cursor: str | None = None) -> dict[str, Any]:
    """Read a bounded plain-text chunk; continue with next_cursor. Changed documents invalidate cursors."""
    return rumors.get(resolve_project_root(), campaign, cursor)


@mcp.tool()
def rumors_create(body: str, campaign: str | None = None) -> dict[str, Any]:
    """Create optional freeform rumors. Campaign accepts canonical/cNNN refs or active fallback."""
    return rumors.write(resolve_project_root(), body, campaign)


@mcp.tool()
def rumors_update(body: str, campaign: str | None = None) -> dict[str, Any]:
    """Replace existing rumors, including for terminal or archived campaigns; body may be empty."""
    return rumors.write(resolve_project_root(), body, campaign, update=True)


@mcp.tool()
def rumors_delete(campaign: str | None = None) -> dict[str, Any]:
    """Delete existing rumors unconditionally, without altering their campaign or any boss."""
    return rumors.delete(resolve_project_root(), campaign)
