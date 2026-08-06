from pathlib import Path

from cac.core import world as world_core
from langchain_core.tools import BaseTool, tool


def build_tools(root: Path) -> list[BaseTool]:
    def get_world() -> dict:
        """Get the project's world summary: its name, globally-assigned lore, and full body."""
        world = world_core.read_world(root)
        return {
            "name": world.metadata.get("name"),
            "assigned_lore": world.metadata.get("assigned_lore", []),
            "body": world.body,
        }

    return [tool(get_world)]
