import asyncio
import re
from pathlib import Path

import frontmatter
import pytest
from cac.cli.app import app
from cac.core import config, skills, templates
from cac.mcp import server
from typer.main import get_command


def test_deploy_skills_creates_all_flavor_files(tmp_path: Path) -> None:
    results = skills.deploy_skills(tmp_path)

    expected_paths = {
        tmp_path / ".claude" / "skills" / "world-manager" / "SKILL.md",
        tmp_path / ".claude" / "skills" / "world-planner" / "SKILL.md",
        tmp_path / ".claude" / "skills" / "campaign-manager" / "SKILL.md",
        tmp_path / ".agents" / "skills" / "world-manager" / "SKILL.md",
        tmp_path / ".agents" / "skills" / "world-planner" / "SKILL.md",
        tmp_path / ".agents" / "skills" / "campaign-manager" / "SKILL.md",
    }
    result_paths = {path for path, _ in results}
    assert result_paths == expected_paths
    assert all(changed for _, changed in results)
    for path in expected_paths:
        assert path.is_file()
        assert path.read_text(encoding="utf-8").startswith("---\n")


def test_deploy_skills_second_run_reports_unchanged(tmp_path: Path) -> None:
    skills.deploy_skills(tmp_path)

    results = skills.deploy_skills(tmp_path)

    assert all(changed is False for _, changed in results)


def test_deploy_skills_overwrites_local_modifications(tmp_path: Path) -> None:
    skills.deploy_skills(tmp_path)
    world_manager_path = tmp_path / ".claude" / "skills" / "world-manager" / "SKILL.md"
    world_manager_path.write_text("locally modified content", encoding="utf-8")

    results = skills.deploy_skills(tmp_path)

    changed_by_path = dict(results)
    assert changed_by_path[world_manager_path] is True
    assert world_manager_path.read_text(encoding="utf-8") != "locally modified content"
    assert world_manager_path.read_text(encoding="utf-8").startswith("---\n")


@pytest.mark.parametrize("flavor", ["claude", "codex"])
@pytest.mark.parametrize("name", config.SKILL_NAMES)
def test_packaged_skill_metadata_and_callable_examples_match_interfaces(flavor, name):
    body = templates.load(f"skills.{flavor}.{name.replace('-', '_')}", "SKILL.md")
    skill = frontmatter.loads(body)
    assert skill["name"] == name and isinstance(skill["description"], str) and skill["description"].strip()
    allowed = {"name", "description", "allowed-tools"} if flavor == "claude" else {"name", "description"}
    assert set(skill.metadata) <= allowed
    if flavor == "claude":
        assert isinstance(skill["allowed-tools"], str)
    tool_names = {tool.name for tool in asyncio.run(server.mcp.list_tools())}
    prefixed = set(re.findall(r"mcp__crypts-and-commits__([a-z_]+)", body))
    assert prefixed <= tool_names
    normalized = body.replace("mcp__crypts-and-commits__", "")
    calls = set(
        re.findall(r"\b((?:boss|campaign|encounter|world|lore|region|prime|rumors|docs|index)_[a-z_]+)\(", normalized)
    )
    assert calls and calls <= tool_names
    cli = get_command(app)
    examples = re.findall(r"\bcac ([a-z-]+) ([a-z-]+)", body)
    assert examples
    for group, command in examples:
        assert group in cli.commands, (name, group)
        assert command in cli.commands[group].commands, (name, group, command)


def test_every_skill_redeployment_preserves_unrelated_files(tmp_path):
    results = skills.deploy_skills(tmp_path)
    original = {path: path.read_bytes() for path, _ in results}
    for path in original:
        path.write_text("Local framework modification", encoding="utf-8")
    unrelated = tmp_path / ".agents" / "skills" / "custom.txt"
    unrelated.write_text("User resource", encoding="utf-8")
    assert all(changed for _, changed in skills.deploy_skills(tmp_path))
    assert all(path.read_bytes() == value for path, value in original.items())
    assert unrelated.read_text(encoding="utf-8") == "User resource"
