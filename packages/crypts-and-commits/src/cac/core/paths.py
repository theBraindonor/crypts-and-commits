from pathlib import Path

from cac.core.config import MCP_CONFIG_FILE_NAME, SOURCEBOOK_DIR_NAME


def sourcebook_dir(root: Path) -> Path:
    return root / SOURCEBOOK_DIR_NAME


def mcp_config_path(root: Path) -> Path:
    return root / MCP_CONFIG_FILE_NAME
