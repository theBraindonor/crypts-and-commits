from typing import Any

from cac.core import references
from cac.core import ruling as ruling_core
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp


@mcp.tool()
@references.inputs("ruling")
def ruling_list(cursor: str | None = None, include_archived: bool = False, status: str | None = None) -> dict[str, Any]:
    """Page canonical ruling names, optionally including archived records or filtering by status
    (recorded, canonized, noted)."""
    names = ruling_core.list_rulings(resolve_project_root(), include_archived=include_archived, status=status)
    return references.identity_page(resolve_project_root(), "ruling", names, cursor)


@mcp.tool()
@references.inputs("ruling")
def ruling_get(name: str, cursor: str | None = None) -> dict[str, Any]:
    """Read a ruling by canonical name. Body is fitted to the response budget; a truncated result carries notice and next_cursor - call
    again with cursor=next_cursor to continue (a cursor fails once the record changes)."""
    return ruling_core.get_payload(resolve_project_root(), name)


@mcp.tool()
@references.inputs("ruling", create=True)
def ruling_create(name: str, body: str, summary: str, origin: str) -> dict[str, Any]:
    """Record a developer ruling named cNNN-eNNN-slug (e000 when no encounter is involved). The cNNN
    campaign must be open and a nonzero eNNN must exist in it. body is required (there is no editor
    fallback over MCP); summary is at most 500 characters; origin is free text."""
    ruling_core.create_ruling(resolve_project_root(), name, body, summary, origin)
    return _read_ruling(name)


@mcp.tool()
@references.inputs("ruling")
def ruling_update(name: str, body: str, summary: str, origin: str) -> dict[str, Any]:
    """Replace a recorded ruling's body, summary, and origin together; body is required."""
    ruling_core.update_ruling(resolve_project_root(), name, body, summary, origin)
    return _read_ruling(name)


@mcp.tool()
@references.inputs("ruling")
def ruling_canonize(name: str, message: str) -> dict[str, Any]:
    """Mark a recorded ruling canonized; message is a required narrative of how the world (lore,
    regions, world summary) was updated."""
    ruling_core.canonize(resolve_project_root(), name, message)
    return _read_ruling(name)


@mcp.tool()
@references.inputs("ruling")
def ruling_note(name: str, message: str) -> dict[str, Any]:
    """Mark a recorded ruling noted; message is a required narrative of why no world update is needed."""
    ruling_core.note(resolve_project_root(), name, message)
    return _read_ruling(name)


@mcp.tool()
@references.inputs("ruling")
def ruling_reopen(name: str, message: str) -> dict[str, Any]:
    """Return an unarchived canonized or noted ruling to recorded, clearing its resolution."""
    ruling_core.reopen(resolve_project_root(), name, message)
    return _read_ruling(name)


@mcp.tool()
@references.inputs("ruling")
def ruling_archive(name: str) -> dict[str, Any]:
    """Archive a canonized or noted ruling; its name stays reserved and readable."""
    ruling_core.archive_ruling(resolve_project_root(), name)
    return _read_ruling(name)


def _read_ruling(name: str) -> dict[str, Any]:
    return ruling_core.get_payload(resolve_project_root(), name)
