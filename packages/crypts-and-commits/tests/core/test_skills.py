from pathlib import Path

from cac.core import skills


def test_deploy_skills_creates_all_flavor_files(tmp_path: Path) -> None:
    results = skills.deploy_skills(tmp_path)

    expected_paths = {
        tmp_path / ".claude" / "skills" / "world-manager" / "SKILL.md",
        tmp_path / ".claude" / "skills" / "campaign-manager" / "SKILL.md",
        tmp_path / ".agents" / "skills" / "world-manager" / "SKILL.md",
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
