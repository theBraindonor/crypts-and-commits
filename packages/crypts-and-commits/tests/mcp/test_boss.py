import pytest
from cac.core import boss, config, world
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
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 500)
    result = api.boss_create("a", "x" * 4000, "Summary")
    assert len(result["body"]) <= 500
    assert "TRUNCATED" in result["body"]
    assert "TRUNCATED" in api.boss_make_available("a")["body"]
    assert "TRUNCATED" in api.boss_update("a", "y" * 4000, "Summary")["body"]
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
