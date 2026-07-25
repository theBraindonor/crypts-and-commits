import json
import os
from pathlib import Path

from cac.core import bootstrap


def test_initialize_creates_sourcebook_directory(tmp_path: Path) -> None:
    sourcebook_dir, created = bootstrap.initialize(tmp_path)

    assert created is True
    assert sourcebook_dir == tmp_path / ".sourcebook"
    assert sourcebook_dir.is_dir()


def test_initialize_is_idempotent(tmp_path: Path) -> None:
    bootstrap.initialize(tmp_path)

    sourcebook_dir, created = bootstrap.initialize(tmp_path)

    assert created is False
    assert sourcebook_dir.is_dir()


def test_resolve_cac_mcp_executable_is_alongside_the_running_interpreter() -> None:
    executable = bootstrap.resolve_cac_mcp_executable()

    expected_name = "cac-mcp.exe" if os.name == "nt" else "cac-mcp"
    assert executable.name == expected_name


def test_initialize_mcp_config_creates_file(tmp_path: Path) -> None:
    path, changed = bootstrap.initialize_mcp_config(tmp_path)

    assert changed is True
    assert path == tmp_path / ".mcp.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    assert config["mcpServers"]["cac"]["command"] == str(bootstrap.resolve_cac_mcp_executable())
    assert config["mcpServers"]["cac"]["args"] == []


def test_initialize_mcp_config_is_idempotent(tmp_path: Path) -> None:
    bootstrap.initialize_mcp_config(tmp_path)

    path, changed = bootstrap.initialize_mcp_config(tmp_path)

    assert changed is False
    assert path.is_file()


def test_initialize_mcp_config_preserves_other_servers(tmp_path: Path) -> None:
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(
        json.dumps({"mcpServers": {"some-other-server": {"command": "/usr/bin/other", "args": ["--flag"]}}}),
        encoding="utf-8",
    )

    bootstrap.initialize_mcp_config(tmp_path)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["mcpServers"]["some-other-server"] == {"command": "/usr/bin/other", "args": ["--flag"]}
    assert "cac" in config["mcpServers"]
