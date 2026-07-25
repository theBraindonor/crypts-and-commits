import json
from pathlib import Path

import pytest
from cac.cli.app import app
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


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
    assert "cac" in config["mcpServers"]


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
    assert "cac" in config["mcpServers"]
