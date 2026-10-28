from typing import Any

from cac.core import budget as budget_core
from cac.core import world as world_core
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp


def world_to_dict(world: world_core.World) -> dict[str, Any]:
    return {"metadata": world.metadata, "body": world.body}


@mcp.tool()
def world_get(cursor: str | None = None) -> dict[str, Any]:
    """Show the current world summary and its frontmatter attributes. Body is fitted to the response budget; a truncated result carries notice and next_cursor - call
    again with cursor=next_cursor to continue (a cursor fails once the record changes)."""
    return budget_core.fit_response(world_core.get_payload(resolve_project_root()), cursor, "world_get")


@mcp.tool()
def world_set(key: str, value: str) -> dict[str, Any]:
    """Set a frontmatter attribute on the world file."""
    return world_to_dict(world_core.set_attribute(resolve_project_root(), key, value))


@mcp.tool()
def world_set_body(body: str) -> dict[str, Any]:
    """Replace the world summary body text."""
    return world_to_dict(world_core.update_body(resolve_project_root(), body))
