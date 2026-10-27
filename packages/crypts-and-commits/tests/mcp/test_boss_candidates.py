import frontmatter
import pytest
from cac.core import boss, boss_candidates, config, world
from cac.mcp.boss import boss_candidates as api_candidates


@pytest.fixture(autouse=True)
def bootstrapped(tmp_path):
    world.initialize_world(tmp_path)


def test_mcp_exposes_empty_structured_contract(tmp_path):
    assert api_candidates() == boss_candidates.candidates(tmp_path)
    result = api_candidates()
    assert set(result) == {
        "items",
        "next_cursor",
        "counts",
        "healthy",
        "diagnostics",
        "diagnostics_omitted",
        "diagnostics_ref",
    }
    assert result["items"] == [] and result["next_cursor"] is None
    assert result["counts"]["total_live"] == 0


def test_mcp_distinguishes_not_ready_blocked_and_eligible(tmp_path):
    for name in ("proposed", "blocked", "eligible", "withdrawn"):
        path = boss.create_boss(tmp_path, name, "Body", "Summary")
        if name in ("blocked", "eligible"):
            boss.make_available(tmp_path, name)
        elif name == "withdrawn":
            boss.withdraw(tmp_path, name)
        if name == "blocked":
            post = frontmatter.load(path)
            post["depends_on"] = ["withdrawn"]
            path.write_text(frontmatter.dumps(post), encoding="utf-8")
    result = api_candidates()
    assert result["counts"] == {
        "total_live": 4,
        "total_archived": 0,
        "pool": 3,
        "eligible": 1,
        "blocked": 1,
        "not_ready": 1,
        "excluded": 1,
        "invalid": 0,
    }
    assert {entry["name"]: entry["classification"] for entry in result["items"]} == {
        "proposed": "not_ready",
        "blocked": "blocked",
        "eligible": "eligible",
    }
    blocked = next(entry for entry in result["items"] if entry["name"] == "blocked")
    assert blocked["reason_codes"] == ["prerequisite_unsatisfied"]
    assert result["healthy"] is True


def test_mcp_budget_and_invalid_cursors(tmp_path, monkeypatch):
    boss.create_boss(tmp_path, "goal", "Body", "Summary")
    with pytest.raises(ValueError):
        api_candidates("bad")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 1200)
    assert len(boss_candidates._json(api_candidates())) <= 1200
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 10)
    with pytest.raises(boss.BossError, match="budget"):
        api_candidates()
