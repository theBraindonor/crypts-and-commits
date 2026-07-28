import contextlib
import io
import json
import os
import runpy
import sys
from pathlib import Path

from cac.core import bootstrap
from tomlkit import parse


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
    assert config["mcpServers"]["crypts-and-commits"]["command"] == str(bootstrap.resolve_cac_mcp_executable())
    assert config["mcpServers"]["crypts-and-commits"]["args"] == []


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
    assert "crypts-and-commits" in config["mcpServers"]


def test_initialize_claude_settings_creates_file(tmp_path: Path) -> None:
    path, changed = bootstrap.initialize_claude_settings(tmp_path)

    assert changed is True
    assert path == tmp_path / ".claude" / "settings.json"
    settings = json.loads(path.read_text(encoding="utf-8"))
    assert settings["permissions"]["allow"] == ["mcp__crypts-and-commits"]
    assert settings["permissions"]["deny"] == ["Edit(.sourcebook/**)"]
    assert settings["enabledMcpjsonServers"] == ["crypts-and-commits"]


def test_initialize_claude_settings_is_idempotent(tmp_path: Path) -> None:
    bootstrap.initialize_claude_settings(tmp_path)

    path, changed = bootstrap.initialize_claude_settings(tmp_path)

    assert changed is False
    settings = json.loads(path.read_text(encoding="utf-8"))
    assert settings["permissions"]["allow"] == ["mcp__crypts-and-commits"]
    assert settings["permissions"]["deny"] == ["Edit(.sourcebook/**)"]
    assert settings["enabledMcpjsonServers"] == ["crypts-and-commits"]


def test_initialize_claude_settings_merges_and_preserves_existing(tmp_path: Path) -> None:
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps(
            {
                "permissions": {
                    "allow": ["Bash(git status)"],
                    "deny": ["Edit(.sourcebook/**)"],
                },
                "model": "some-model",
            }
        ),
        encoding="utf-8",
    )

    path, changed = bootstrap.initialize_claude_settings(tmp_path)

    assert changed is True
    settings = json.loads(path.read_text(encoding="utf-8"))
    assert settings["model"] == "some-model"
    assert settings["permissions"]["allow"] == ["Bash(git status)", "mcp__crypts-and-commits"]
    assert settings["permissions"]["deny"] == ["Edit(.sourcebook/**)"]
    assert settings["enabledMcpjsonServers"] == ["crypts-and-commits"]


def test_initialize_codex_config_creates_file(tmp_path: Path) -> None:
    path, changed = bootstrap.initialize_codex_config(tmp_path)

    assert changed is True
    assert path == tmp_path / ".codex" / "config.toml"
    config = parse(path.read_text(encoding="utf-8"))
    server = config["mcp_servers"]["crypts-and-commits"]
    assert server["command"] == str(bootstrap.resolve_cac_mcp_executable())
    assert server["args"] == []
    assert server["default_tools_approval_mode"] == "approve"
    guard_group = config["hooks"]["PreToolUse"][0]
    assert guard_group["matcher"] == "^(Bash|apply_patch)$"
    guard_hook = guard_group["hooks"][0]
    assert guard_hook["command"] == "python3 .codex/hooks/sourcebook_guard.py"
    assert guard_hook["command_windows"] == r"py -3 .codex\hooks\sourcebook_guard.py"


def test_initialize_codex_config_is_idempotent(tmp_path: Path) -> None:
    bootstrap.initialize_codex_config(tmp_path)

    path, changed = bootstrap.initialize_codex_config(tmp_path)

    assert changed is False
    assert path.is_file()


def test_initialize_codex_config_merges_and_preserves_existing(tmp_path: Path) -> None:
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '# Keep this comment.\nmodel = "some-model"\n\n[mcp_servers.other]\ncommand = "other-mcp"\n\n'
        '[mcp_servers.crypts-and-commits]\ncustom_setting = "keep-me"\ncommand = "stale"\n',
        encoding="utf-8",
    )

    path, changed = bootstrap.initialize_codex_config(tmp_path)

    assert changed is True
    content = path.read_text(encoding="utf-8")
    assert "# Keep this comment." in content
    config = parse(content)
    assert config["model"] == "some-model"
    assert config["mcp_servers"]["other"]["command"] == "other-mcp"
    server = config["mcp_servers"]["crypts-and-commits"]
    assert server["custom_setting"] == "keep-me"
    assert server["command"] == str(bootstrap.resolve_cac_mcp_executable())
    assert server["args"] == []
    assert server["default_tools_approval_mode"] == "approve"
    assert config["hooks"]["PreToolUse"][0]["matcher"] == "^(Bash|apply_patch)$"


def test_initialize_codex_config_preserves_existing_hooks_and_is_idempotent(tmp_path: Path) -> None:
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '[[hooks.PreToolUse]]\nmatcher = "Bash"\n\n[[hooks.PreToolUse.hooks]]\n'
        'type = "command"\ncommand = "existing-hook"\n',
        encoding="utf-8",
    )

    bootstrap.initialize_codex_config(tmp_path)
    path, changed = bootstrap.initialize_codex_config(tmp_path)

    assert changed is False
    config = parse(path.read_text(encoding="utf-8"))
    groups = config["hooks"]["PreToolUse"]
    assert len(groups) == 2
    assert groups[0]["hooks"][0]["command"] == "existing-hook"
    assert groups[1]["hooks"][0]["command"] == "python3 .codex/hooks/sourcebook_guard.py"


def _run_guard_hook(path: Path, event: dict[str, object], monkeypatch) -> str:
    output = io.StringIO()
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(event)))
    with contextlib.redirect_stdout(output):
        runpy.run_path(str(path), run_name="__main__")
    return output.getvalue()


def test_initialize_codex_guard_hook_deploys_and_is_idempotent(tmp_path: Path) -> None:
    path, changed = bootstrap.initialize_codex_guard_hook(tmp_path)

    assert changed is True
    assert path == tmp_path / ".codex" / "hooks" / "sourcebook_guard.py"
    assert "permissionDecision" in path.read_text(encoding="utf-8")

    path, changed = bootstrap.initialize_codex_guard_hook(tmp_path)

    assert changed is False
    assert path.is_file()


def test_codex_guard_hook_denies_direct_sourcebook_access(tmp_path: Path, monkeypatch) -> None:
    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)

    output = _run_guard_hook(
        path,
        {"tool_name": "Bash", "tool_input": {"command": "Get-Content .sourcebook/world.md"}},
        monkeypatch,
    )

    response = json.loads(output)
    assert response["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_codex_guard_hook_denies_sourcebook_patches(tmp_path: Path, monkeypatch) -> None:
    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)

    output = _run_guard_hook(
        path,
        {"tool_name": "apply_patch", "tool_input": {"command": "*** Update File: .sourcebook/world.md"}},
        monkeypatch,
    )

    response = json.loads(output)
    assert response["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_codex_guard_hook_allows_unrelated_commands(tmp_path: Path, monkeypatch) -> None:
    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)

    output = _run_guard_hook(
        path,
        {"tool_name": "Bash", "tool_input": {"command": "pdm run pytest -q"}},
        monkeypatch,
    )

    assert output == ""
