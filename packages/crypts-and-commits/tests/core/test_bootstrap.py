import contextlib
import io
import json
import os
import runpy
import sys
from pathlib import Path

import pytest
from cac.core import bootstrap
from tomlkit import parse, table


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
    assert guard_group["matcher"] == "^apply_patch$"
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
    assert config["hooks"]["PreToolUse"][0]["matcher"] == "^apply_patch$"


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


@pytest.mark.parametrize("tool", ["Bash", "exec_command", "write_stdin", "other_tool"])
def test_codex_guard_hook_allows_shell_sourcebook_references(tmp_path: Path, monkeypatch, tool: str) -> None:
    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)

    output = _run_guard_hook(
        path,
        {"tool_name": tool, "tool_input": {"command": "Get-Content .sourcebook/world.md"}},
        monkeypatch,
    )

    assert output == ""


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


@pytest.mark.parametrize("operation", ["Add File", "Update File", "Delete File", "Move to"])
@pytest.mark.parametrize(
    "target",
    [
        ".sourcebook/world.md",
        "./.sourcebook/world.md",
        "docs/../.sourcebook/world.md",
        "../.sourcebook/world.md",
        ".sourcebook",
        "/repo/.sourcebook/world.md",
        r"C:\repo\.sourcebook\world.md",
        r"C:\repo\docs\..\.SOURCEBOOK\world.md",
        r"\\server\share\.sourcebook\world.md",
    ],
)
def test_codex_guard_checks_all_file_operation_targets(
    tmp_path: Path, monkeypatch, operation: str, target: str
) -> None:
    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)
    patch = f"*** Begin Patch\n*** {operation}: {target}\n*** End Patch\n"
    output = _run_guard_hook(path, {"tool_name": "apply_patch", "tool_input": {"command": patch}}, monkeypatch)

    result = json.loads(output)["hookSpecificOutput"]
    assert result["hookEventName"] == "PreToolUse"
    assert result["permissionDecision"] == "deny"
    assert "MCP" in result["permissionDecisionReason"]


@pytest.mark.parametrize("direction", ["into", "out-of", "later-file"])
def test_codex_guard_checks_moves_and_all_files(tmp_path: Path, monkeypatch, direction: str) -> None:
    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)
    if direction == "into":
        operations = "*** Update File: ordinary.md\n*** Move to: .sourcebook/world.md\n@@\n-old\n+new\n"
    elif direction == "out-of":
        operations = "*** Update File: .sourcebook/world.md\n*** Move to: ordinary.md\n@@\n-old\n+new\n"
    else:
        operations = "*** Add File: ordinary.md\n+text\n*** Delete File: .sourcebook/world.md\n"
    patch = f"*** Begin Patch\n{operations}*** End Patch\n"

    output = _run_guard_hook(path, {"tool_name": "apply_patch", "tool_input": patch}, monkeypatch)

    assert json.loads(output)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize(
    "target", ["README.md", ".sourcebook-backup/world.md", "docs/.sourcebook.md", ".sourcebook/../ordinary.md"]
)
def test_codex_guard_allows_incidental_patch_content(tmp_path: Path, monkeypatch, target: str) -> None:
    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)
    patch = (
        f"*** Begin Patch\n*** Update File: {target}\n@@\n"
        " Read .sourcebook/world.md through CAC.\n"
        "-*** Delete File: .sourcebook/world.md\n"
        "+*** Update File: .sourcebook/world.md\n"
        "+text\v*** Delete File: .sourcebook/world.md\n"
        "*** End Patch\n"
    )

    output = _run_guard_hook(path, {"tool_name": "apply_patch", "tool_input": {"command": patch}}, monkeypatch)

    assert output == ""


def test_codex_guard_uses_native_case_rules_for_posix_paths(tmp_path: Path, monkeypatch) -> None:
    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)
    event = {"tool_name": "apply_patch", "tool_input": {"command": "*** Delete File: .SOURCEBOOK/world.md\r\n"}}

    output = _run_guard_hook(path, event, monkeypatch)

    if os.name == "nt":
        assert json.loads(output)["hookSpecificOutput"]["permissionDecision"] == "deny"
    else:
        assert output == ""


@pytest.mark.parametrize(
    "event",
    [
        None,
        [],
        {},
        {"tool_name": "apply_patch"},
        {"tool_name": "apply_patch", "tool_input": []},
        {"tool_name": "apply_patch", "tool_input": {"command": None}},
        {"tool_name": "apply_patch", "tool_input": {"command": "not a patch"}},
    ],
)
def test_codex_guard_ignores_unsupported_payloads(tmp_path: Path, monkeypatch, event: object) -> None:
    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)

    assert _run_guard_hook(path, event, monkeypatch) == ""


def test_codex_guard_ignores_malformed_json(tmp_path: Path, monkeypatch) -> None:
    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)
    monkeypatch.setattr(sys, "stdin", io.StringIO("{invalid"))
    output = io.StringIO()

    with contextlib.redirect_stdout(output):
        runpy.run_path(str(path), run_name="__main__")

    assert output.getvalue() == ""


@pytest.mark.parametrize("shared_group", [False, True])
def test_codex_config_upgrades_legacy_guard_and_preserves_unrelated_hooks(tmp_path: Path, shared_group: bool) -> None:
    path, _ = bootstrap.initialize_codex_config(tmp_path)
    config = parse(path.read_text(encoding="utf-8"))
    guard_group = config["hooks"]["PreToolUse"][0]
    guard_group["matcher"] = "^(Bash|apply_patch)$"
    guard_group["hooks"][0]["timeout"] = 12
    if shared_group:
        unrelated = table()
        unrelated["type"] = "command"
        unrelated["command"] = "unrelated-hook"
        guard_group["hooks"].append(unrelated)
    path.write_text(config.as_string(), encoding="utf-8")

    path, changed = bootstrap.initialize_codex_config(tmp_path)

    assert changed is True
    groups = parse(path.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
    guards = [g for g in groups if any(h.get("command") == bootstrap._CODEX_GUARD_HOOK_COMMAND for h in g["hooks"])]
    assert len(guards) == 1
    assert guards[0]["matcher"] == "^apply_patch$"
    assert guards[0]["hooks"][0]["timeout"] == 12
    if shared_group:
        assert groups[0]["matcher"] == "^(Bash|apply_patch)$"
        assert [h["command"] for h in groups[0]["hooks"]] == ["unrelated-hook"]
    else:
        assert len(groups) == 1
    before = path.read_bytes()
    assert bootstrap.initialize_codex_config(tmp_path)[1] is False
    assert path.read_bytes() == before


def test_codex_config_removes_duplicate_guard_registrations(tmp_path: Path) -> None:
    from copy import deepcopy

    path, _ = bootstrap.initialize_codex_config(tmp_path)
    config = parse(path.read_text(encoding="utf-8"))
    groups = config["hooks"]["PreToolUse"]
    duplicate = deepcopy(groups[0])
    duplicate["matcher"] = "^(Bash|apply_patch)$"
    groups.append(duplicate)
    groups.append(deepcopy(groups[0]))
    path.write_text(config.as_string(), encoding="utf-8")

    assert bootstrap.initialize_codex_config(tmp_path)[1] is True
    groups = parse(path.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
    assert len(groups) == 1
    assert groups[0]["matcher"] == "^apply_patch$"
    assert len(groups[0]["hooks"]) == 1
    assert bootstrap.initialize_codex_config(tmp_path)[1] is False


def test_codex_guard_template_replaces_old_deployed_script(tmp_path: Path) -> None:
    from cac.core import templates

    path, _ = bootstrap.initialize_codex_guard_hook(tmp_path)
    path.write_text("old broad guard", encoding="utf-8")

    assert bootstrap.initialize_codex_guard_hook(tmp_path)[1] is True
    assert path.read_text(encoding="utf-8") == templates.load("codex", "sourcebook_guard.py")
