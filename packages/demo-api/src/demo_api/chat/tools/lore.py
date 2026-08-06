from pathlib import Path

from cac.core import lore as lore_core
from langchain_core.tools import BaseTool, tool


def build_tools(root: Path) -> list[BaseTool]:
    def list_lore() -> list[str]:
        """List all lore entry names."""
        return lore_core.list_lore(root)

    def get_lore(name: str) -> dict:
        """Get a lore entry's enabled state, world/region assignment, and full body by name."""
        metadata, body = lore_core.read_metadata(root, name)
        return {
            "name": metadata.get("name", name),
            "enabled": metadata.get("enabled", True),
            "assigned_to_world": metadata.get("assigned_to_world", False),
            "assigned_regions": metadata.get(lore_core.ASSIGNED_REGIONS_KEY, []),
            "body": body,
        }

    return [tool(list_lore), tool(get_lore)]
