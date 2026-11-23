import re

import pytest
from cac.cli.app import app
from cac.core import docs as docs_core
from typer.testing import CliRunner

runner = CliRunner()


def test_list_shows_registered_docs() -> None:
    result = runner.invoke(app, ["docs", "list"])

    assert result.exit_code == 0
    for name, _ in docs_core.list_docs():
        assert name in result.output


def test_get_shows_full_body() -> None:
    result = runner.invoke(app, ["docs", "get", "workflow"])

    assert result.exit_code == 0
    assert "Crypts and Commits Workflow Index" in result.output


def test_get_shows_migration_guide_body() -> None:
    result = runner.invoke(app, ["docs", "get", "migration-guide"])

    assert result.exit_code == 0
    assert "Crypts and Commits Sourcebook Migration Guide" in result.output


@pytest.mark.parametrize("name", [name for name, _ in docs_core.list_docs()])
def test_get_preserves_complete_guide(name: str) -> None:
    result = runner.invoke(app, ["docs", "get", name])

    assert result.exit_code == 0
    assert docs_core.read_doc(name).strip() == result.output.strip()
    assert "[TRUNCATED" not in result.output


def test_get_missing_doc_fails() -> None:
    result = runner.invoke(app, ["docs", "get", "missing"])

    assert result.exit_code == 1


def test_get_truncates_body_over_dedicated_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("cac.cli.docs.DOCS_RESPONSE_BUDGET", 50)

    result = runner.invoke(app, ["docs", "get", "workflow"])

    assert result.exit_code == 0
    assert "[TRUNCATED" in result.output and "next_cursor: " in result.output
    assert str(docs_core.doc_source_path("workflow")) not in result.output


def test_list_pages_break_at_the_same_items_as_mcp(monkeypatch: pytest.MonkeyPatch) -> None:
    from cac.core.references import encoded
    from cac.mcp import docs as mcp_docs

    items = [{"name": name, "summary": summary} for name, summary in docs_core.list_docs()]
    largest = max(len(encoded(item)) for item in items)
    monkeypatch.setattr(
        "cac.core.config.RESPONSE_BUDGET", len(encoded({"items": [], "next_cursor": "6"})) + 2 * largest + 2
    )
    names = {item["name"] for item in items}

    cli_pages, cursor = [], None
    while True:
        result = runner.invoke(app, ["docs", "list"] + ([] if cursor is None else ["--cursor", cursor]))
        assert result.exit_code == 0
        hint = re.search(r"pass --cursor (\S+) to continue", result.output)
        cursor = hint[1] if hint else None
        listed = [match[1] for match in re.finditer(r"^([a-z-]+): ", result.output, re.MULTILINE) if match[1] in names]
        cli_pages.append((listed, cursor))
        if cursor is None:
            break

    mcp_pages, cursor = [], None
    while True:
        page = mcp_docs.docs_list(cursor)
        mcp_pages.append(([item["name"] for item in page["items"]], page["next_cursor"]))
        cursor = page["next_cursor"]
        if cursor is None:
            break

    assert cli_pages == mcp_pages
    assert len(cli_pages) > 1
