import json
import os
import sysconfig
from pathlib import Path
from typing import Any

from cac.core.config import CAC_MCP_SCRIPT_NAME, MCP_SERVER_NAME
from cac.core.paths import mcp_config_path, sourcebook_dir


def initialize(root: Path) -> tuple[Path, bool]:
    """Create the .sourcebook directory under root.

    Returns the sourcebook directory path and whether it was newly created.
    """
    directory = sourcebook_dir(root)
    created = not directory.exists()
    directory.mkdir(exist_ok=True)
    return directory, created


def resolve_cac_mcp_executable() -> Path:
    """Resolve the cac-mcp console script installed alongside the running interpreter.

    Console scripts are installed into the interpreter's own scripts directory
    (a venv's Scripts/bin folder), which is not necessarily on PATH - so the path is
    derived from the running interpreter rather than assumed to be resolvable by name.
    """
    scripts_dir = Path(sysconfig.get_path("scripts"))
    filename = f"{CAC_MCP_SCRIPT_NAME}.exe" if os.name == "nt" else CAC_MCP_SCRIPT_NAME
    return scripts_dir / filename


def initialize_mcp_config(root: Path) -> tuple[Path, bool]:
    """Write, or merge into, .mcp.json at the project root, registering the cac MCP server
    at its actual installed path. Existing entries for other servers are preserved.

    Returns the config path and whether the cac entry was newly added or changed.
    """
    path = mcp_config_path(root)
    config: dict[str, Any] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    servers = config.setdefault("mcpServers", {})
    entry = {"command": str(resolve_cac_mcp_executable()), "args": []}
    changed = servers.get(MCP_SERVER_NAME) != entry
    servers[MCP_SERVER_NAME] = entry

    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path, changed
