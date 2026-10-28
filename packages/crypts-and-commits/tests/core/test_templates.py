from cac.core import templates


def test_load_workflow_reference_guide() -> None:
    content = templates.load("docs", "workflow.md")

    assert content.startswith("# Crypts and Commits Workflow Reference Guide")


def test_load_tool_reference() -> None:
    content = templates.load("docs", "tool-reference.md")

    assert content.startswith("# Crypts and Commits Tool Reference")
