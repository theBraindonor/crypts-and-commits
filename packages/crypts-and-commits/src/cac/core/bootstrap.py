import json
import os
import sysconfig
from pathlib import Path
from typing import Any

from tomlkit import document, parse, table

from cac.core.config import CAC_MCP_SCRIPT_NAME, MCP_SERVER_NAME, SOURCEBOOK_DIR_NAME
from cac.core.paths import claude_settings_path, codex_config_path, mcp_config_path, sourcebook_dir


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
    """Write, or merge into, .mcp.json at the project root, registering the
    crypts-and-commits MCP server at its actual installed path. Existing entries for
    other servers are preserved.

    Returns the config path and whether the crypts-and-commits entry was newly added or changed.
    """
    path = mcp_config_path(root)
    config: dict[str, Any] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    servers = config.setdefault("mcpServers", {})
    entry = {"command": str(resolve_cac_mcp_executable()), "args": []}
    changed = servers.get(MCP_SERVER_NAME) != entry
    servers[MCP_SERVER_NAME] = entry

    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path, changed


def initialize_claude_settings(root: Path) -> tuple[Path, bool]:
    """Write, or merge into, .claude/settings.json at the project root: allow the
    crypts-and-commits MCP server's tools, deny direct Edit access to
    .sourcebook, and trust the .mcp.json crypts-and-commits entry. Existing keys and
    list entries are preserved.

    Returns the settings path and whether anything was newly added.
    """
    path = claude_settings_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    settings: dict[str, Any] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    permissions = settings.setdefault("permissions", {})
    allow = permissions.setdefault("allow", [])
    deny = permissions.setdefault("deny", [])
    enabled_servers = settings.setdefault("enabledMcpjsonServers", [])

    changed = False
    for entry, entries in (
        (f"mcp__{MCP_SERVER_NAME}", allow),
        (f"Edit({SOURCEBOOK_DIR_NAME}/**)", deny),
    ):
        if entry not in entries:
            entries.append(entry)
            changed = True
    if MCP_SERVER_NAME not in enabled_servers:
        enabled_servers.append(MCP_SERVER_NAME)
        changed = True

    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return path, changed


def initialize_codex_config(root: Path) -> tuple[Path, bool]:
    """Write, or merge into, .codex/config.toml at the project root.

    Registers the crypts-and-commits MCP server while preserving unrelated
    Codex configuration and TOML document formatting where possible. Returns
    the config path and whether the document was changed.
    """
    path = codex_config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    config = parse(path.read_text(encoding="utf-8")) if path.exists() else document()

    changed = False
    servers = config.get("mcp_servers")
    if servers is None:
        servers = table()
        config["mcp_servers"] = servers
        changed = True

    server = servers.get(MCP_SERVER_NAME)
    if server is None:
        server = table()
        servers[MCP_SERVER_NAME] = server
        changed = True

    required_settings = {
        "command": str(resolve_cac_mcp_executable()),
        "args": [],
        "default_tools_approval_mode": "approve",
    }
    for key, value in required_settings.items():
        if server.get(key) != value:
            server[key] = value
            changed = True

    if changed:
        path.write_text(config.as_string(), encoding="utf-8")
    return path, changed
