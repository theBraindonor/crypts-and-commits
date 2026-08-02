import pytest
from cac.core import docs as docs_core
from cac.mcp import docs as mcp_docs


def test_docs_list_returns_name_and_summary() -> None:
    result = mcp_docs.docs_list()

    assert {"name": "workflow", "summary": docs_core.doc_summary("workflow")} in result["items"]
    assert result["next_cursor"] is None


def test_docs_get_returns_full_body() -> None:
    result = mcp_docs.docs_get("workflow")

    assert result["name"] == "workflow"
    assert result["summary"] == docs_core.doc_summary("workflow")
    assert result["body"] == docs_core.read_doc("workflow")
    assert "[TRUNCATED" not in result["body"]


def test_docs_get_missing_raises() -> None:
    with pytest.raises(docs_core.DocNotFoundError):
        mcp_docs.docs_get("missing")


def test_docs_get_truncates_over_dedicated_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("cac.mcp.docs.DOCS_RESPONSE_BUDGET", 50)

    result = mcp_docs.docs_get("workflow")

    assert "[TRUNCATED" in result["body"]
    assert str(docs_core.doc_source_path("workflow")) in result["body"]
