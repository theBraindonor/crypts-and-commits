from typing import Any

from cac.core import budget as budget_core
from cac.core import lore as lore_core
from cac.core import region as region_core
from cac.core import world as world_core
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp
from cac.mcp.region import region_to_dict
from cac.mcp.world import world_to_dict


def lore_to_dict(lore: lore_core.Lore) -> dict[str, Any]:
    return {"name": lore.name, "body": lore.body}


@mcp.tool()
def lore_get(name: str, cursor: str | None = None) -> dict[str, Any]:
    """Show a lore entry's frontmatter attributes, summary, and body - a standard, convention, or
    best practice used to review an encounter's plan before work begins. Body is fitted to the response budget; a truncated result carries notice and next_cursor - call
    again with cursor=next_cursor to continue (a cursor fails once the record changes)."""
    return budget_core.fit_response(lore_core.get_payload(resolve_project_root(), name), cursor, "lore_get")


@mcp.tool()
def lore_list(cursor: str | None = None) -> dict[str, Any]:
    """List lore names in .sourcebook/lore, paged under the response budget. Pass the returned
    next_cursor to resume."""
    names = lore_core.list_lore(resolve_project_root())
    page = budget_core.paginate(names, cursor)
    return {"items": page.items, "next_cursor": page.next_cursor}


@mcp.tool()
def lore_create(name: str, body: str, summary: str) -> dict[str, Any]:
    """Create a new lore file. summary is a required short routing summary (max 500 characters)
    stored alongside the body."""
    root = resolve_project_root()
    lore_core.create_lore(root, name, body, summary)
    return lore_to_dict(lore_core.read_lore(root, name))


@mcp.tool()
def lore_update(name: str, body: str, summary: str) -> dict[str, Any]:
    """Replace an existing lore file's body, regenerating its summary in the same write."""
    root = resolve_project_root()
    lore_core.update_lore(root, name, body, summary)
    return lore_to_dict(lore_core.read_lore(root, name))


@mcp.tool()
def lore_delete(name: str) -> dict[str, str]:
    """Delete a lore file."""
    path = lore_core.delete_lore(resolve_project_root(), name)
    return {"deleted": str(path)}


@mcp.tool()
def lore_set_summary(name: str, summary: str) -> dict[str, Any]:
    """Set a lore file's summary (max 500 characters)."""
    return lore_to_dict(lore_core.set_summary(resolve_project_root(), name, summary))


@mcp.tool()
def lore_assign_world(name: str) -> dict[str, Any]:
    """Assign a lore file to the world, making it apply globally to every encounter."""
    return world_to_dict(world_core.assign_lore(resolve_project_root(), name))


@mcp.tool()
def lore_unassign_world(name: str) -> dict[str, Any]:
    """Unassign a lore file from the world."""
    return world_to_dict(world_core.unassign_lore(resolve_project_root(), name))


@mcp.tool()
def lore_assign_region(name: str, region: str) -> dict[str, Any]:
    """Assign a lore file to a region, so it applies to encounters assigned to that region."""
    return region_to_dict(region_core.assign_lore(resolve_project_root(), region, name))


@mcp.tool()
def lore_unassign_region(name: str, region: str) -> dict[str, Any]:
    """Unassign a lore file from a region."""
    return region_to_dict(region_core.unassign_lore(resolve_project_root(), region, name))


@mcp.tool()
def lore_enable(name: str) -> dict[str, Any]:
    """Enable a lore file so it is included when resolving applicable lore."""
    return lore_to_dict(lore_core.set_enabled(resolve_project_root(), name, True))


@mcp.tool()
def lore_disable(name: str) -> dict[str, Any]:
    """Disable a lore file so it is excluded when resolving applicable lore."""
    return lore_to_dict(lore_core.set_enabled(resolve_project_root(), name, False))
