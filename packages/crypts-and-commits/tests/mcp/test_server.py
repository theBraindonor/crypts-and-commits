import asyncio

from cac.mcp.instance import mcp
from cac.mcp.server import main  # noqa: F401  -- import triggers world/prime registration


def test_all_domain_tools_are_registered() -> None:
    tools = asyncio.run(mcp.list_tools())
    tool_names = {tool.name for tool in tools}

    assert tool_names == {
        "world_get",
        "world_set",
        "world_set_body",
        "prime_get",
        "prime_applicable_lore",
    }
