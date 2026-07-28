import json
from pathlib import Path

import pytest
from cac.cli.app import app
from cac.core import bootstrap as bootstrap_core
from cac.core import git_utils
from tomlkit import parse
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def test_init_fails_cleanly_when_git_identity_unresolvable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("git user.name is not configured.")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 1
    assert not isinstance(result.exception, git_utils.GitIdentityError)
    assert not (tmp_path / ".sourcebook" / "world.md").exists()


def test_init_creates_sourcebook_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook").is_dir()


def test_init_creates_world_file(tmp_path: Path) -> None:
    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    assert (tmp_path / ".sourcebook" / "world.md").is_file()


def test_init_does_not_overwrite_existing_world_file(tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    world_file = tmp_path / ".sourcebook" / "world.md"
    world_file.write_text("---\nname: keep-me\n---\n\nCustom body.\n", encoding="utf-8")

    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    assert "keep-me" in world_file.read_text(encoding="utf-8")


def test_init_shows_splash() -> None:
    result = runner.invoke(app, ["bootstrap", "init"])

    assert "Crypts And Commits" in result.output
    assert "A Code Assistant Continuity Framework" in result.output


def test_init_creates_mcp_config(tmp_path: Path) -> None:
    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    mcp_config = tmp_path / ".mcp.json"
    assert mcp_config.is_file()
    config = json.loads(mcp_config.read_text(encoding="utf-8"))
    assert "crypts-and-commits" in config["mcpServers"]


def test_init_preserves_other_mcp_servers(tmp_path: Path) -> None:
    mcp_config = tmp_path / ".mcp.json"
    mcp_config.write_text(
        json.dumps({"mcpServers": {"some-other-server": {"command": "/usr/bin/other", "args": []}}}),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    config = json.loads(mcp_config.read_text(encoding="utf-8"))
    assert "some-other-server" in config["mcpServers"]
    assert "crypts-and-commits" in config["mcpServers"]


def test_init_creates_claude_settings(tmp_path: Path) -> None:
    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    settings_path = tmp_path / ".claude" / "settings.json"
    assert settings_path.is_file()
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["permissions"]["allow"] == ["mcp__crypts-and-commits"]
    assert settings["permissions"]["deny"] == ["Edit(.sourcebook/**)"]
    assert settings["enabledMcpjsonServers"] == ["crypts-and-commits"]


def test_init_preserves_other_claude_settings(tmp_path: Path) -> None:
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(json.dumps({"model": "some-model"}), encoding="utf-8")

    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["model"] == "some-model"
    assert "mcp__crypts-and-commits" in settings["permissions"]["allow"]


def test_init_creates_codex_config(tmp_path: Path) -> None:
    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    config_path = tmp_path / ".codex" / "config.toml"
    assert config_path.is_file()
    server = parse(config_path.read_text(encoding="utf-8"))["mcp_servers"]["crypts-and-commits"]
    assert server["command"] == str(bootstrap_core.resolve_cac_mcp_executable())
    assert server["args"] == []
    assert server["default_tools_approval_mode"] == "approve"


def test_init_deploys_agent_skills(tmp_path: Path) -> None:
    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    for base_dir in (".claude", ".agents"):
        for name in ("world-manager", "campaign-manager"):
            skill_path = tmp_path / base_dir / "skills" / name / "SKILL.md"
            assert skill_path.is_file()
            assert skill_path.read_text(encoding="utf-8").startswith("---\n")


def test_init_redeploys_agent_skills_over_local_edits(tmp_path: Path) -> None:
    runner.invoke(app, ["bootstrap", "init"])
    skill_path = tmp_path / ".claude" / "skills" / "world-manager" / "SKILL.md"
    skill_path.write_text("locally modified content", encoding="utf-8")

    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    assert skill_path.read_text(encoding="utf-8") != "locally modified content"


def test_init_merges_existing_codex_config(tmp_path: Path) -> None:
    config_path = tmp_path / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        'model = "some-model"\n\n[mcp_servers.other]\ncommand = "other-mcp"\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["bootstrap", "init"])

    assert result.exit_code == 0
    config = parse(config_path.read_text(encoding="utf-8"))
    assert config["model"] == "some-model"
    assert config["mcp_servers"]["other"]["command"] == "other-mcp"
    assert config["mcp_servers"]["crypts-and-commits"]["default_tools_approval_mode"] == "approve"
