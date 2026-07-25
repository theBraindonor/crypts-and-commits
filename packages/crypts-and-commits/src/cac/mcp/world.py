from pathlib import Path
from typing import Any

from cac.core import world as world_core
from cac.mcp.instance import mcp


def world_to_dict(world: world_core.World) -> dict[str, Any]:
    return {"metadata": world.metadata, "body": world.body}


@mcp.tool()
def world_get() -> dict[str, Any]:
    """Show the current world summary and its frontmatter attributes."""
    return world_to_dict(world_core.read_world(Path.cwd()))


@mcp.tool()
def world_set(key: str, value: str) -> dict[str, Any]:
    """Set a frontmatter attribute on the world file."""
    return world_to_dict(world_core.set_attribute(Path.cwd(), key, value))


@mcp.tool()
def world_set_body(body: str) -> dict[str, Any]:
    """Replace the world summary body text."""
    return world_to_dict(world_core.update_body(Path.cwd(), body))
