from cac.core import config, docs, templates
from cac.mcp import docs as api


def test_boss_template_and_paired_docs_remain_packaged_and_readable():
    assert "## Success Criteria" in templates.load("sourcebook", "boss.md")
    guide = docs.read_doc("workflow")
    assert "## Bosses" in guide
    assert "### Candidate discovery" in guide
    assert "### Promotion and campaign coupling" in guide
    assert "### Reconciliation examples" in guide
    reference = docs.read_doc("tool-reference")
    assert "### Short references" in reference
    assert "### Operation/input matrix" in reference
    assert "### Candidate page" in reference
    assert "boss_candidates" in reference
    assert "boss_assign_campaign" in reference and "campaign_reactivate" in reference
    for name, body in (("workflow", guide), ("tool-reference", reference)):
        assert len(body) <= config.DOCS_RESPONSE_BUDGET
        assert api.docs_get(name)["body"] == body
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
        "record",
    ):
        assert f"boss_{operation}" in reference
