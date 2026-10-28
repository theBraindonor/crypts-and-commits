import pytest
from cac.cli.app import app
from cac.core import docs as docs_core
from typer.testing import CliRunner

runner = CliRunner()


def test_list_shows_registered_docs() -> None:
    result = runner.invoke(app, ["docs", "list"])

    assert result.exit_code == 0
    assert "workflow" in result.output
    assert "migration-guide" in result.output
    assert "branching-guide" in result.output
    assert "tool-reference" in result.output


def test_get_shows_full_body() -> None:
    result = runner.invoke(app, ["docs", "get", "workflow"])

    assert result.exit_code == 0
    assert "Crypts and Commits Workflow Reference Guide" in result.output


def test_get_shows_migration_guide_body() -> None:
    result = runner.invoke(app, ["docs", "get", "migration-guide"])

    assert result.exit_code == 0
    assert "Crypts and Commits Sourcebook Migration Guide" in result.output


@pytest.mark.parametrize("name", ["workflow", "tool-reference", "branching-guide", "migration-guide"])
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
