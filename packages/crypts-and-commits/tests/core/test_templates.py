from cac.core import templates


def test_load_workflow_reference_guide() -> None:
    content = templates.load("docs", "workflow.md")

    assert content.startswith("# Crypts and Commits Workflow Reference Guide")
