import json
import re
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
    assert "tool-reference" in names
    assert "planning-workflow" in names
    assert "development-workflow" in names


@pytest.mark.parametrize("name", [name for name, _ in docs.list_docs()])
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

    assert "Workflow Index" in summary


def test_tool_reference_doc_returns_full_body() -> None:
    assert docs.read_doc("tool-reference").startswith("# Crypts and Commits Tool Reference")
    assert "Tool Reference" in docs.doc_summary("tool-reference")


@pytest.mark.parametrize("name", [name for name, _ in docs.list_docs() if "workflow" in name])
def test_workflows_leave_contracts_to_tool_reference_with_headroom(name: str) -> None:
    body = docs.read_doc(name)

    assert "(tool-reference.md)" in body
    assert len(body) <= 40_000


@pytest.mark.parametrize("name", ["workflow", "planning-workflow", "development-workflow", "tool-reference"])
def test_paired_docs_ship_no_repository_campaign_or_encounter_names(name: str) -> None:
    body = docs.read_doc(name)

    # e000 is the reserved "no encounter" marker in ruling names, not a repository encounter.
    assert re.search(r"(?<!\w)(?!e000)[ce]0\d\d(?!\w)|boss-edition", body) is None


def test_doc_summary_missing_raises() -> None:
    with pytest.raises(docs.DocNotFoundError):
        docs.doc_summary("missing")


def test_read_doc_returns_full_body() -> None:
    body = docs.read_doc("workflow")

    assert body.startswith("# Crypts and Commits Workflow Index")


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


@pytest.mark.parametrize("name", ["branching-guide", "migration-guide"])
def test_supporting_guides_describe_rulings(name: str) -> None:
    body = docs.read_doc(name)

    assert "ruling_create" in body
    if name == "migration-guide":
        assert "Rulings are additive within schema version 1." in body


@pytest.mark.parametrize("name", [name for name, _ in docs.list_docs()])
def test_guides_never_narrow_canonize_to_lore(name: str) -> None:
    body = " ".join(docs.read_doc(name).split())  # catch phrases broken across wrapped lines

    assert "rulings into lore" not in body
    assert "name no lore records" not in body


def test_phase_workflows_preserve_the_shared_authorization_exception() -> None:
    paragraphs = []
    for name in ("planning-workflow", "development-workflow"):
        body = docs.read_doc(name)
        paragraph = re.search(r"Not separately gated:.*?(?=\n\n)", body, re.DOTALL)
        assert paragraph is not None, name
        text = " ".join(paragraph.group().split())
        for rule in ("draft-to-reviewed", "ruling capture", "campaign transitions", "lore, region and world edits"):
            assert rule in text, (name, rule)
        assert "subject to the authorization rules" in text
        assert "Agent planning and campaign workflow" in text
        assert "## Agent planning and campaign workflow" in body
        paragraphs.append(text)
    assert paragraphs[0] == paragraphs[1]


def test_workflow_index_routes_to_self_contained_phase_guides() -> None:
    body = docs.read_doc("workflow")
    for name in ("planning-workflow", "development-workflow"):
        assert f"({name}.md)" in body
        assert f'docs_get("{name}")' in body
    assert "## Encounter" not in body
    assert "## Bosses" not in body


def test_page_docs_measures_compact_json_items_after_reserving_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    items = [{"name": name, "summary": summary} for name, summary in docs.list_docs()]
    encoded = [len(json.dumps(item, ensure_ascii=False, separators=(",", ":"))) + 1 for item in items]
    reserve = len(json.dumps({"items": [], "next_cursor": str(len(items))}, separators=(",", ":")))
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", reserve + encoded[0] + encoded[1])

    first = docs.page_docs(None)

    assert first.items == items[:2]
    assert first.next_cursor == "2"
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", reserve + encoded[0] + encoded[1] - 1)
    assert docs.page_docs(None).items == items[:1]
