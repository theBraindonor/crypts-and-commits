import pytest
from cac.core import boss, config, references, world
from cac.mcp import boss as api


@pytest.fixture(autouse=True)
def bootstrapped(tmp_path):
    world.initialize_world(tmp_path)


def test_all_operations_and_structured_results():
    result = api.boss_create("goal", "[tool.ruff]", "[summary]")
    assert result["metadata"]["status"] == "proposed"
    assert result["body"] == "[tool.ruff]"
    assert result["summary"] == "[summary]"
    assert "summary" not in result["metadata"]
    api.boss_create("other", "Other", "Other")
    assert api.boss_make_available("goal")["metadata"]["status"] == "available"
    assert api.boss_assign_dependency("goal", "other")["metadata"]["depends_on"] == ["other"]
    assert api.boss_unassign_dependency("goal", "other")["metadata"]["depends_on"] == []
    assert api.boss_update("goal", "New body", "New summary")["body"] == "New body"
    assert api.boss_withdraw("goal")["metadata"]["status"] == "withdrawn"
    assert api.boss_reactivate("goal")["metadata"]["status"] == "proposed"
    api.boss_withdraw("goal")
    assert api.boss_archive("goal")["metadata"]["archived"] is True
    assert api.boss_list() == {
        "items": ["other"],
        "next_cursor": None,
        "identities": [{"canonical": "other", "short": None, "reason": "unnumbered"}],
    }
    assert api.boss_list(include_archived=True)["items"] == ["goal", "other"]
    assert api.boss_get("goal")["metadata"]["status"] == "withdrawn"
    with pytest.raises(boss.BossError):
        api.boss_reactivate("goal")


def test_paging_and_all_body_responses_budgeted(monkeypatch):
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 1000)
    result = api.boss_create("a", "x" * 4000, "Summary")
    assert len(references.encoded(result)) <= 1000
    assert "TRUNCATED" in result["notice"]
    assert "TRUNCATED" in api.boss_make_available("a")["notice"]
    assert "TRUNCATED" in api.boss_update("a", "y" * 4000, "Summary")["notice"]
    api.boss_create("b", "Body", "Summary")
    api.boss_withdraw("b")
    api.boss_archive("b")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 150)
    first = api.boss_list(include_archived=True)
    assert first == {
        "items": ["a"],
        "next_cursor": "1",
        "identities": [{"canonical": "a", "short": None, "reason": "unnumbered"}],
    }
    assert api.boss_list(first["next_cursor"], include_archived=True) == {
        "items": ["b"],
        "next_cursor": None,
        "identities": [{"canonical": "b", "short": None, "reason": "unnumbered"}],
    }
    with pytest.raises(ValueError):
        api.boss_list("invalid")


def test_core_errors_propagate_without_writes(tmp_path):
    api.boss_create("goal", "Body", "Summary")
    before = boss.boss_path(tmp_path, "goal").read_bytes()
    with pytest.raises(boss.BossNotFoundError):
        api.boss_assign_dependency("goal", "missing")
    with pytest.raises(ValueError):
        api.boss_update("goal", "New", "x" * 501)
    assert boss.boss_path(tmp_path, "goal").read_bytes() == before


def test_roadmap_recording_and_historical_archive(tmp_path):
    result = api.boss_record(
        "b001-old", "[Evidence] café", "Existing goal", "completed", "roadmap.md", "Shipped", "2024-02-29"
    )
    assert result["metadata"]["status"] == "vanquished"
    assert result["metadata"]["provenance"]["completed_on"] == "2024-02-29"
    assert result["identity"]["short"] == "b001"
    result = api.boss_record("b002-next", "Next", "Next", "planned", "roadmap.md", "Future", depends_on=["b001"])
    assert result["metadata"]["depends_on"] == ["b001-old"]
    assert result["metadata"]["status"] == "proposed"
    result = api.boss_archive("b001")
    assert result["metadata"]["archived"] and result["metadata"]["status"] == "vanquished"
    assert api.boss_get("b001")["metadata"]["provenance"]["source"] == "roadmap.md"
    assert api.boss_candidates()["items"][0]["prerequisites"][0]["completion_origin"] == "roadmap"
    with pytest.raises(boss.BossAlreadyExistsError):
        api.boss_record("b001-old", "Replacement", "Replacement", "planned", "Source", "Reason")


def test_recorded_boss_whole_envelope_budget_and_preflight(tmp_path, monkeypatch):
    from cac.core import references

    monkeypatch.setattr(config, "RESPONSE_BUDGET", 1600)
    result = api.boss_record("b001-old", ('"\\\n' * 3000), "Summary", "completed", "Source", "Outcome")
    assert len(references.encoded(result)) <= 1600
    assert "TRUNCATED" in result["notice"] and "boss_get" in result["notice"]
    assert result["metadata"]["provenance"]["message"] == "Outcome"
    assert result["identity"]["canonical"] == "b001-old"
    with pytest.raises(ValueError, match="before writes"):
        api.boss_record("b002-huge", "Body", "Summary", "planned", "s" * 5000, "Reason")
    assert boss.list_bosses(tmp_path) == ["b001-old"]
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 100)
    with pytest.raises(ValueError, match="response budget"):
        api.boss_get("b001")


@pytest.mark.parametrize("progress", ["planned", "in_progress", "completed"])
def test_record_arguments_fail_before_mutation(tmp_path, progress):
    with pytest.raises(ValueError):
        api.boss_record("b001-old", "Body", "Summary", progress, " ", "Evidence")
    assert boss.list_bosses(tmp_path) == []
