from pathlib import Path

from cac.core.config import (
    CLAUDE_SETTINGS_FILE_NAME,
    CODEX_CONFIG_FILE_NAME,
    MCP_CONFIG_FILE_NAME,
    SEARCH_INDEX_DB_NAME,
    SEARCH_INDEX_DIR_NAME,
    SOURCEBOOK_DIR_NAME,
)


def sourcebook_dir(root: Path) -> Path:
    return root / SOURCEBOOK_DIR_NAME


def resolve_project_root(start: Path | None = None) -> Path:
    """Find the project root by walking upward from `start` (default cwd) for the
    nearest ancestor, inclusive of `start` itself, that already contains a
    `.sourcebook/` directory - mirroring how `git` locates a repository root from
    any subdirectory. Falls back to `start` unchanged when no ancestor qualifies,
    preserving today's "not bootstrapped" errors for a genuinely unbootstrapped
    location."""
    candidate = start if start is not None else Path.cwd()
    for directory in (candidate, *candidate.parents):
        if sourcebook_dir(directory).is_dir():
            return directory
    return candidate


def search_index_db_path(root: Path) -> Path:
    return sourcebook_dir(root) / SEARCH_INDEX_DIR_NAME / SEARCH_INDEX_DB_NAME


def mcp_config_path(root: Path) -> Path:
    return root / MCP_CONFIG_FILE_NAME


def claude_settings_path(root: Path) -> Path:
    return root / CLAUDE_SETTINGS_FILE_NAME


def codex_config_path(root: Path) -> Path:
    return root / CODEX_CONFIG_FILE_NAME
