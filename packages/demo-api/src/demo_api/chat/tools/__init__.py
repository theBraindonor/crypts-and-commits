from pathlib import Path

from langchain_core.tools import BaseTool

from demo_api.chat.tools import campaigns, encounters

_BUILDERS = [campaigns.build_tools, encounters.build_tools]


def build_tools(root: Path) -> list[BaseTool]:
    """Assemble every registered domain's tools, bound to root. Add a new domain by adding a
    `build_tools(root)` module here and appending it to _BUILDERS."""
    return [t for builder in _BUILDERS for t in builder(root)]
