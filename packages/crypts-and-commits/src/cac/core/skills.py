from pathlib import Path

from cac.core import templates
from cac.core.config import CLAUDE_SKILLS_DIR_NAME, CODEX_SKILLS_DIR_NAME, SKILL_FILE_NAME, SKILL_NAMES

_TEMPLATE_PACKAGE = "skills"
_FLAVOR_DIRS = (
    ("claude", CLAUDE_SKILLS_DIR_NAME),
    ("codex", CODEX_SKILLS_DIR_NAME),
)


def deploy_skills(root: Path) -> list[tuple[Path, bool]]:
    """Deploy the packaged agent skills into a target project.

    Every deployed file is overwritten unconditionally on each call, unlike
    world.md's create-if-missing semantics - skill files are framework-owned,
    not user-editable data, so re-running this must propagate updates shipped
    in a newer cac release. Returns a (path, changed) pair per deployed file.
    """
    results: list[tuple[Path, bool]] = []
    for name in SKILL_NAMES:
        package_segment = name.replace("-", "_")
        for flavor, dir_name in _FLAVOR_DIRS:
            content = templates.load(f"{_TEMPLATE_PACKAGE}.{flavor}.{package_segment}", SKILL_FILE_NAME)
            path = root / dir_name / name / SKILL_FILE_NAME
            path.parent.mkdir(parents=True, exist_ok=True)
            changed = not path.exists() or path.read_text(encoding="utf-8") != content
            if changed:
                path.write_text(content, encoding="utf-8")
            results.append((path, changed))
    return results
