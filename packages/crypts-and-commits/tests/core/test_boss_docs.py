from cac.core import config, docs, templates
from cac.mcp import docs as api


def test_boss_template_and_workflow_remain_packaged_and_readable():
    assert "## Success Criteria" in templates.load("sourcebook", "boss.md")
    guide = docs.read_doc("workflow")
    assert "## Boss planning records" in guide
    assert "### Candidate discovery" in guide
    assert "boss_candidates" in guide
    assert "## Numbered references and canonical identity" in guide
    assert "### Operation/input matrix" in guide
    assert len(guide) <= config.DOCS_RESPONSE_BUDGET
    assert api.docs_get("workflow")["body"] == guide
    for operation in (
        "create",
        "get",
        "list",
        "update",
        "make_available",
        "withdraw",
        "reactivate",
        "archive",
        "assign_dependency",
        "unassign_dependency",
    ):
        assert f"boss_{operation}" in guide
