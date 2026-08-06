from pathlib import Path

from cac.core import region as region_core
from langchain_core.tools import BaseTool, tool


def build_tools(root: Path) -> list[BaseTool]:
    def list_regions() -> list[str]:
        """List all region names."""
        return region_core.list_regions(root)

    def get_region(name: str) -> dict:
        """Get a region's documented path, assigned lore, and full body by name."""
        metadata, body = region_core.read_metadata(root, name)
        return {
            "name": metadata.get("name", name),
            "path": metadata.get("path", ""),
            "assigned_lore": metadata.get(region_core.ASSIGNED_LORE_KEY, []),
            "body": body,
        }

    return [tool(list_regions), tool(get_region)]
