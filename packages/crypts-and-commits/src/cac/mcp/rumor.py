from typing import Any

from cac.core import references
from cac.core import rumor as rumor_core
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp


@mcp.tool()
@references.inputs("rumor")
def rumor_list(cursor: str | None = None, include_archived: bool = False, status: str | None = None) -> dict[str, Any]:
    """Page canonical rumor names, optionally including archived records or filtering by status."""
    names = rumor_core.list_rumors(resolve_project_root(), include_archived=include_archived, status=status)
    return references.identity_page(resolve_project_root(), "rumor", names, cursor)


@mcp.tool()
@references.inputs("rumor")
def rumor_get(name: str, cursor: str | None = None) -> dict[str, Any]:
    """Read a rumor by canonical name or numbered short reference. Body is fitted to the response budget; a truncated result carries notice and next_cursor - call
    again with cursor=next_cursor to continue (a cursor fails once the record changes)."""
    return rumor_core.get_payload(resolve_project_root(), name)


@mcp.tool()
@references.inputs("rumor", create=True)
def rumor_create(name: str, body: str, summary: str, origin: str) -> dict[str, Any]:
    """Create an open rumor with body, routing summary (maximum 500 characters), and free-text origin."""
    rumor_core.create_rumor(resolve_project_root(), name, body, summary, origin)
    return _read_rumor(name)


@mcp.tool()
@references.inputs("rumor")
def rumor_update(name: str, body: str, summary: str, origin: str) -> dict[str, Any]:
    """Replace an open rumor's body, summary, and origin together."""
    rumor_core.update_rumor(resolve_project_root(), name, body, summary, origin)
    return _read_rumor(name)


@mcp.tool()
@references.inputs("rumor")
def rumor_promote(name: str, boss: str, message: str | None = None) -> dict[str, Any]:
    """Link an open rumor to an existing unassigned proposed/available boss; the boss record is never written."""
    rumor_core.promote(resolve_project_root(), name, boss, message)
    return _read_rumor(name)


@mcp.tool()
@references.inputs("rumor")
def rumor_dismiss(name: str, message: str) -> dict[str, Any]:
    """Dismiss an open rumor with a required reason."""
    rumor_core.dismiss(resolve_project_root(), name, message)
    return _read_rumor(name)


@mcp.tool()
@references.inputs("rumor")
def rumor_reopen(name: str, message: str) -> dict[str, Any]:
    """Return an unarchived promoted or dismissed rumor to open, clearing its boss link and resolution."""
    rumor_core.reopen(resolve_project_root(), name, message)
    return _read_rumor(name)


@mcp.tool()
@references.inputs("rumor")
def rumor_archive(name: str) -> dict[str, Any]:
    """Archive a promoted or dismissed rumor; its name stays reserved and readable."""
    rumor_core.archive_rumor(resolve_project_root(), name)
    return _read_rumor(name)


@mcp.tool()
@references.inputs("rumor")
def rumor_renumber(name: str, new_name: str) -> dict[str, Any]:
    """Rename a live open or dismissed rumor to an unused literal name; promoted rumors keep their number."""
    rumor_core.renumber(resolve_project_root(), name, new_name)
    return _read_rumor(new_name)


def _read_rumor(name: str) -> dict[str, Any]:
    return rumor_core.get_payload(resolve_project_root(), name)
