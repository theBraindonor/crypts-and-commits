from typing import Any

from cac.core import budget as budget_core
from cac.core import region as region_core
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp


def region_to_dict(region: region_core.Region) -> dict[str, Any]:
    return {"name": region.name, "path": region.path, "body": region.body}


@mcp.tool()
def region_get(name: str, cursor: str | None = None) -> dict[str, Any]:
    """Show a region's frontmatter attributes, summary, and body - a documented path within the
    repository that can carry its own lore. Body is fitted to the response budget; a truncated result carries notice and next_cursor - call
    again with cursor=next_cursor to continue (a cursor fails once the record changes)."""
    return budget_core.fit_response(region_core.get_payload(resolve_project_root(), name), cursor, "region_get")


@mcp.tool()
def region_list(cursor: str | None = None) -> dict[str, Any]:
    """List region names in .sourcebook/region, paged under the response budget."""
    names = region_core.list_regions(resolve_project_root())
    page = budget_core.paginate(names, cursor)
    return {"items": page.items, "next_cursor": page.next_cursor}


@mcp.tool()
def region_create(name: str, body: str, summary: str, path: str = "") -> dict[str, Any]:
    """Create a new region file. summary is a required short routing summary (max 500 characters);
    path is the repository path this region covers (not validated against the filesystem - regions
    may be aspirational)."""
    root = resolve_project_root()
    region_core.create_region(root, name, body, summary, path)
    return region_to_dict(region_core.read_region(root, name))


@mcp.tool()
def region_update(name: str, body: str, summary: str) -> dict[str, Any]:
    """Replace an existing region's body, regenerating its summary in the same write."""
    root = resolve_project_root()
    region_core.update_region(root, name, body, summary)
    return region_to_dict(region_core.read_region(root, name))


@mcp.tool()
def region_delete(name: str) -> dict[str, str]:
    """Delete a region file."""
    path = region_core.delete_region(resolve_project_root(), name)
    return {"deleted": str(path)}


@mcp.tool()
def region_set_summary(name: str, summary: str) -> dict[str, Any]:
    """Set a region's summary (max 500 characters)."""
    return region_to_dict(region_core.set_summary(resolve_project_root(), name, summary))


@mcp.tool()
def region_set_path(name: str, path: str) -> dict[str, Any]:
    """Set the repository path a region covers."""
    return region_to_dict(region_core.set_path(resolve_project_root(), name, path))
