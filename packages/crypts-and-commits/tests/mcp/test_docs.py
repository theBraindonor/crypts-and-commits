import pytest
from cac.core import docs as docs_core
from cac.mcp import docs as mcp_docs


def test_docs_list_returns_name_and_summary() -> None:
    result = mcp_docs.docs_list()

    assert {"name": "workflow", "summary": docs_core.doc_summary("workflow")} in result["items"]
    assert {"name": "migration-guide", "summary": docs_core.doc_summary("migration-guide")} in result["items"]
    assert {"name": "branching-guide", "summary": docs_core.doc_summary("branching-guide")} in result["items"]
    assert result["next_cursor"] is None


@pytest.mark.parametrize("name", ["workflow", "branching-guide", "migration-guide"])
def test_docs_get_returns_full_body(name: str) -> None:
    result = mcp_docs.docs_get(name)

    assert result["name"] == name
    assert result["summary"] == docs_core.doc_summary(name)
    assert result["body"] == docs_core.read_doc(name)
    assert "[TRUNCATED" not in result["body"]


def test_docs_get_returns_migration_guide_body() -> None:
    result = mcp_docs.docs_get("migration-guide")

    assert result["name"] == "migration-guide"
    assert result["body"] == docs_core.read_doc("migration-guide")


def test_docs_get_missing_raises() -> None:
    with pytest.raises(docs_core.DocNotFoundError):
        mcp_docs.docs_get("missing")


@pytest.mark.parametrize("name", ["workflow", "branching-guide", "migration-guide"])
def test_docs_get_truncates_over_dedicated_budget(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    monkeypatch.setattr("cac.mcp.docs.DOCS_RESPONSE_BUDGET", 50)

    result = mcp_docs.docs_get(name)

    assert "[TRUNCATED" in result["body"]
    assert str(docs_core.doc_source_path(name)) in result["body"]


def test_docs_list_pages_all_registered_guides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 1)
    cursor = None
    items = []
    while True:
        page = mcp_docs.docs_list(cursor)
        items.extend(page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break

    assert items == [{"name": name, "summary": summary} for name, summary in docs_core.list_docs()]
