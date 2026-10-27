from pathlib import Path

import pytest
from cac.core import config, docs


def test_list_docs_returns_registered_entries() -> None:
    items = docs.list_docs()

    names = [name for name, _ in items]
    assert names == sorted(names)
    assert "workflow" in names
    assert "migration-guide" in names
    assert "branching-guide" in names


@pytest.mark.parametrize("name", ["branching-guide", "migration-guide", "workflow"])
def test_registered_guide_resource_fits_response_budget(name: str) -> None:
    path = docs.doc_source_path(name)
    body = docs.read_doc(name)

    assert path.is_file()
    assert path.name == f"{name}.md"
    assert body == path.read_text(encoding="utf-8")
    assert 0 < len(body) <= config.DOCS_RESPONSE_BUDGET
    assert dict(docs.list_docs())[name] == docs.doc_summary(name)


def test_doc_summary_returns_registered_summary() -> None:
    summary = docs.doc_summary("workflow")

    assert "Workflow Reference Guide" in summary


def test_doc_summary_missing_raises() -> None:
    with pytest.raises(docs.DocNotFoundError):
        docs.doc_summary("missing")


def test_read_doc_returns_full_body() -> None:
    body = docs.read_doc("workflow")

    assert body.startswith("# Crypts and Commits Workflow Reference Guide")


def test_read_doc_missing_raises() -> None:
    with pytest.raises(docs.DocNotFoundError):
        docs.read_doc("missing")


def test_doc_source_path_points_at_real_file() -> None:
    path = docs.doc_source_path("workflow")

    assert isinstance(path, Path)
    assert path.name == "workflow.md"
    assert path.is_file()


def test_doc_source_path_missing_raises() -> None:
    with pytest.raises(docs.DocNotFoundError):
        docs.doc_source_path("missing")


def test_migration_guide_doc_summary_returns_registered_summary() -> None:
    summary = docs.doc_summary("migration-guide")

    assert "Migration Guide" in summary


def test_migration_guide_doc_returns_full_body() -> None:
    body = docs.read_doc("migration-guide")

    assert body.startswith("# Crypts and Commits Sourcebook Migration Guide")
    assert "Current sourcebook schema version: 1" in body
    assert "guardrail" in body
