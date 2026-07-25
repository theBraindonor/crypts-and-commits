from pathlib import Path

from cac.core.config import CLAUDE_SETTINGS_FILE_NAME, CODEX_CONFIG_FILE_NAME, MCP_CONFIG_FILE_NAME, SOURCEBOOK_DIR_NAME


def sourcebook_dir(root: Path) -> Path:
    return root / SOURCEBOOK_DIR_NAME


def mcp_config_path(root: Path) -> Path:
    return root / MCP_CONFIG_FILE_NAME


def claude_settings_path(root: Path) -> Path:
    return root / CLAUDE_SETTINGS_FILE_NAME


def codex_config_path(root: Path) -> Path:
    return root / CODEX_CONFIG_FILE_NAME
