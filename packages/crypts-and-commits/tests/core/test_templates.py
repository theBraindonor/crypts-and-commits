import pytest
from cac.core import templates


@pytest.mark.parametrize(
    ("name", "title"),
    [
        ("workflow", "Workflow Index"),
        ("planning-workflow", "Planning Workflow"),
        ("development-workflow", "Development Workflow"),
    ],
)
def test_load_workflow_guides(name: str, title: str) -> None:
    content = templates.load("docs", f"{name}.md")

    assert content.startswith(f"# Crypts and Commits {title}")


def test_load_tool_reference() -> None:
    content = templates.load("docs", "tool-reference.md")

    assert content.startswith("# Crypts and Commits Tool Reference")
