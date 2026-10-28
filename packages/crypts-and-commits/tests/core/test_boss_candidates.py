"""Candidate discovery includes test-only future/corrupt records in temporary stores."""

import json

import frontmatter
import pytest
from cac.core import boss, campaign, config, search_index, world
from cac.core import boss_candidates as discovery


@pytest.fixture(autouse=True)
def bootstrapped(tmp_path):
    world.initialize_world(tmp_path)


def goal(root, name="goal", *, status="available", archived=False, **metadata):
    path = boss.create_boss(root, name, "Body is never discovery output.", "[routing] summary")
    post = frontmatter.load(path)
    post.metadata.update(status=status, archived=archived, **metadata)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    if archived:
        target = boss.boss_dir(root, archived=True) / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        path.rename(target)
        path = target
    return path


def set_metadata(path, **metadata):
    post = frontmatter.load(path)
    post.metadata.update(metadata)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")


def linked_campaign(root, name, boss_name, status="open", archived=False):
    # Fixture-only partial/future links must not bypass public creation claim guards.
    path = campaign.campaign_dir(root) / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    post = frontmatter.Post(
        "Campaign body should not appear.", name=name, boss=boss_name, status=status, archived=archived
    )
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    if archived:
        target = campaign.archive_campaign_dir(root) / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        path.rename(target)
        return target
    return path


def item(result, name="goal"):
    return next(entry for entry in result["items"] if entry["name"] == name)


def codes(entries):
    return {entry["code"] for entry in entries}


def snapshot(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_missing_empty_and_unbootstrapped_collection(tmp_path):
    before = snapshot(tmp_path)
    result = discovery.candidates(tmp_path)
    assert result["items"] == []
    assert result["counts"] == {
        "total_live": 0,
        "total_archived": 0,
        "pool": 0,
        "eligible": 0,
        "blocked": 0,
        "not_ready": 0,
        "excluded": 0,
        "invalid": 0,
    }
    assert result["healthy"] is True and result["diagnostics"] == []
    assert snapshot(tmp_path) == before
    assert not boss.boss_dir(tmp_path).exists()
    world.world_path(tmp_path).unlink()
    with pytest.raises(FileNotFoundError):
        discovery.candidates(tmp_path)


@pytest.mark.parametrize("status", config.BOSS_STATUSES)
@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("assigned", [False, True])
def test_root_state_matrix(tmp_path, status, archived, assigned):
    goal(tmp_path, status=status, archived=archived, **({"campaign": "selected"} if assigned else {}))
    if assigned:
        linked_campaign(
            tmp_path, "selected", "goal", status="completed" if status == "vanquished" else "open", archived=archived
        )
    before = snapshot(tmp_path)
    result = discovery.candidates(tmp_path)
    assert result["counts"]["total_archived"] == int(archived)
    if not archived and not assigned and status in ("available", "proposed"):
        entry = item(result)
        assert entry["eligible"] == (status == "available")
        assert entry["classification"] == ("eligible" if status == "available" else "not_ready")
    else:
        assert result["items"] == []
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("status", config.BOSS_STATUSES)
@pytest.mark.parametrize("archived", [False, True])
def test_prerequisite_state_matrix(tmp_path, status, archived):
    goal(tmp_path, "prerequisite", status=status, archived=archived)
    goal(tmp_path, depends_on=["prerequisite"])
    entry = item(discovery.candidates(tmp_path))
    assert entry["eligible"] == (status == "vanquished")
    assert entry["prerequisites"][0] == {
        "name": "prerequisite",
        "status": status,
        "archived": archived,
        "satisfied": status == "vanquished",
    }
    assert entry["unsatisfied_count"] == (0 if status == "vanquished" else 1)


def test_diamond_and_deep_graph_are_iterative_and_read_only(tmp_path):
    # Construct temporary fixtures directly to keep this a graph test rather than
    # repeatedly invoking create's full inventory for every node.
    directory = boss.boss_dir(tmp_path)
    directory.mkdir()
    for number in range(1050):
        name = f"node-{number}"
        post = frontmatter.Post(
            "Secret body",
            name=name,
            status="vanquished",
            archived=False,
            summary="Summary",
            depends_on=[f"node-{number + 1}"] if number < 1049 else [],
        )
        (directory / f"{name}.md").write_text(frontmatter.dumps(post), encoding="utf-8")
    goal(tmp_path, "left", status="vanquished", depends_on=["node-0"])
    goal(tmp_path, "right", status="vanquished", depends_on=["node-0"])
    goal(tmp_path, depends_on=["left", "right"])
    before = snapshot(tmp_path)
    assert item(discovery.candidates(tmp_path))["eligible"] is True
    assert snapshot(tmp_path) == before
    set_metadata(directory / "node-1049.md", depends_on=["node-500"])
    result = discovery.candidates(tmp_path)
    assert item(result)["eligible"] is False
    assert result["healthy"] is False
    assert "dependency_integrity" in codes(item(result)["diagnostics"])


@pytest.mark.parametrize(
    "dependencies,code",
    [
        (None, "invalid_dependencies"),
        ("name", "invalid_dependencies"),
        ([{}], "invalid_dependencies"),
        (["../escape"], "invalid_dependencies"),
        (["missing"], "missing_prerequisite"),
        (["goal"], "self_dependency"),
        (["other", "other"], "duplicate_dependency"),
    ],
)
def test_graph_damage_blocks_root_without_writes(tmp_path, dependencies, code):
    goal(tmp_path, "other", status="vanquished")
    goal(tmp_path, depends_on=dependencies)
    before = snapshot(tmp_path)
    result = discovery.candidates(tmp_path)
    entry = item(result)
    assert entry["classification"] == "blocked"
    assert code in codes(entry["diagnostics"])
    assert result["healthy"] is False
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "damage", [{"name": "wrong"}, {"status": "unknown"}, {"archived": True}, {"archived": "false"}, {"campaign": []}]
)
def test_invalid_records_are_not_silently_discarded(tmp_path, damage):
    path = goal(tmp_path)
    set_metadata(path, **damage)
    result = discovery.candidates(tmp_path)
    assert result["healthy"] is False
    assert result["counts"]["invalid"] == 1
    assert "invalid_record" in codes(result["diagnostics"])
    assert result["items"] == []


def test_unrelated_damage_visible_without_hiding_valid_goals(tmp_path):
    goal(tmp_path)
    goal(tmp_path, "retired", status="withdrawn", depends_on=["missing"])
    result = discovery.candidates(tmp_path)
    assert item(result)["eligible"] is True
    assert result["healthy"] is False
    assert result["counts"]["excluded"] == 1
    assert result["diagnostics"][0]["name"] == "retired"


def test_reachable_invalid_record_blocks_dependent(tmp_path):
    path = goal(tmp_path, "done", status="vanquished")
    set_metadata(path, status="invalid")
    goal(tmp_path, depends_on=["done"])
    assert item(discovery.candidates(tmp_path))["eligible"] is False


@pytest.mark.parametrize("campaign_status", config.CAMPAIGN_STATUSES)
@pytest.mark.parametrize("boss_status", ["available", "vanquished"])
def test_link_context_and_lifecycle_consistency(tmp_path, campaign_status, boss_status):
    goal(tmp_path, "prerequisite", status=boss_status, campaign="attempt")
    linked_campaign(tmp_path, "attempt", "prerequisite", campaign_status)
    goal(tmp_path, depends_on=["prerequisite"])
    result = discovery.candidates(tmp_path)
    detail = item(result)["prerequisites"][0]
    assert detail["campaign"] == "attempt"
    assert detail["campaign_status"] == campaign_status
    consistent = (boss_status == "available" and campaign_status in ("draft", "open", "paused")) or (
        boss_status == "vanquished" and campaign_status == "completed"
    )
    assert result["healthy"] == consistent
    assert item(result)["eligible"] == (consistent and boss_status == "vanquished")


@pytest.mark.parametrize(
    "defect,code",
    [
        ("missing", "campaign_not_found"),
        ("reciprocal", "campaign_boss_mismatch"),
        ("ambiguous", "ambiguous_campaign"),
        ("bad-name", "invalid_campaign_link"),
        ("bad-status", "invalid_campaign_record"),
        ("archive-flag", "invalid_campaign_record"),
    ],
)
def test_broken_campaign_links_block_dependents(tmp_path, defect, code):
    goal(tmp_path, "done", status="vanquished", campaign="../escape" if defect == "bad-name" else "attempt")
    if defect not in ("missing", "bad-name"):
        path = linked_campaign(tmp_path, "attempt", "other" if defect == "reciprocal" else "done", "completed")
        if defect == "ambiguous":
            destination = campaign.archive_campaign_dir(tmp_path) / path.name
            destination.parent.mkdir(parents=True)
            destination.write_bytes(path.read_bytes())
        elif defect == "bad-status":
            set_metadata(path, status="bogus")
        elif defect == "archive-flag":
            set_metadata(path, archived=True)
    goal(tmp_path, depends_on=["done"])
    result = discovery.candidates(tmp_path)
    assert item(result)["eligible"] is False
    assert code in codes(result["diagnostics"])


def test_archived_campaign_and_boss_resolve_as_prerequisite(tmp_path):
    goal(tmp_path, "done", status="vanquished", archived=True, campaign="attempt")
    linked_campaign(tmp_path, "attempt", "done", "completed", archived=True)
    goal(tmp_path, depends_on=["done"])
    result = discovery.candidates(tmp_path)
    assert item(result)["eligible"] is True
    assert result["healthy"] is True


def test_numeric_order_ties_legacy_and_paging_counts(tmp_path, monkeypatch):
    names = ["b1000-goal", "b999-goal", "b010-z", "b002-b", "b002-a", "legacy", "Alpha"]
    for name in names:
        goal(tmp_path, name)
    expected = ["b002-a", "b002-b", "b010-z", "b999-goal", "b1000-goal", "Alpha", "legacy"]
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 1300)
    gathered, cursor, counts = [], None, None
    while True:
        result = discovery.candidates(tmp_path, cursor)
        assert len(discovery._json(result)) <= config.RESPONSE_BUDGET
        counts = counts or result["counts"]
        assert result["counts"] == counts
        gathered.extend(entry["name"] for entry in result["items"])
        cursor = result["next_cursor"]
        if cursor is None:
            break
    assert gathered == expected
    assert counts["eligible"] == 7
    for invalid in ("bad", "-1", "8"):
        with pytest.raises(ValueError):
            discovery.candidates(tmp_path, invalid)


def test_large_details_and_diagnostics_remain_bounded(tmp_path, monkeypatch):
    targets = [f"missing-{number}" for number in range(150)]
    goal(tmp_path, depends_on=targets, summary="x" * 10000)
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 1800)
    result = discovery.candidates(tmp_path)
    entry = item(result)
    assert len(discovery._json(result)) <= 1800
    assert entry["eligible"] is False
    assert entry["unsatisfied_count"] == 150
    assert entry["prerequisite_count"] == 150
    assert entry["prerequisites_omitted"] > 0
    assert entry["summary_truncated"] is True
    assert result["diagnostics_omitted"] > 0
    assert result["healthy"] is False
    assert entry["ref"] == "boss_get"
    assert result["diagnostics_ref"] == "boss_list"
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 32)
    with pytest.raises(boss.BossError, match="budget"):
        discovery.candidates(tmp_path)


def test_collection_ambiguity_errors_and_nested_directory_exclusion(tmp_path):
    live = goal(tmp_path)
    nested = boss.boss_dir(tmp_path) / "notes"
    nested.mkdir()
    (nested / "b999-not-a-boss.md").write_text("Not a boss", encoding="utf-8")
    assert discovery.candidates(tmp_path)["counts"]["total_live"] == 1
    archived = boss.boss_dir(tmp_path, archived=True) / live.name
    archived.parent.mkdir(parents=True)
    archived.write_bytes(live.read_bytes())
    before = snapshot(tmp_path)
    with pytest.raises(boss.BossError, match="Ambiguous"):
        discovery.candidates(tmp_path)
    assert snapshot(tmp_path) == before


def test_index_and_audit_are_unchanged(tmp_path):
    goal(tmp_path)
    search_index.rebuild_index(tmp_path)
    before = snapshot(tmp_path)
    result = discovery.candidates(tmp_path)
    assert snapshot(tmp_path) == before
    assert "Body is never discovery output" not in json.dumps(result)


def test_varied_serialized_budgets_preserve_flags_names_and_paging(tmp_path, monkeypatch):
    for name in ("b002-" + "long" * 25, "b010-goal", "legacy"):
        goal(tmp_path, name, depends_on=[f"missing-{i}" for i in range(30)], summary='[quoted] "Unicode café"' * 10)
    evaluated = discovery._evaluate(tmp_path)
    monkeypatch.setattr(discovery, "_evaluate", lambda root: evaluated)
    for limit in (32, 600, 1000, 1500, 1800, 2500, 4000, 20000):
        monkeypatch.setattr(config, "RESPONSE_BUDGET", limit)
        cursor, names = None, []
        try:
            while True:
                result = discovery.candidates(tmp_path, cursor)
                assert len(discovery._json(result)) <= limit
                assert result["healthy"] is False
                assert result["counts"]["blocked"] == 3
                for entry in result["items"]:
                    assert entry["eligible"] is False
                    assert entry["unsatisfied_count"] == 30
                    assert "prerequisite_unsatisfied" in entry["reason_codes"]
                    names.append(entry["name"])
                cursor = result["next_cursor"]
                if cursor is None:
                    break
            assert names == [entry["name"] for entry in evaluated[0]]
        except boss.BossError as exc:
            assert limit < 1500
            assert "budget" in str(exc)


def test_malformed_yaml_and_summary_are_explicit_diagnostics(tmp_path):
    path = goal(tmp_path, "broken")
    path.write_text("---\nstatus: [unclosed\n---\nBody", encoding="utf-8")
    goal(tmp_path, summary={"not": "text"})
    result = discovery.candidates(tmp_path)
    assert result["healthy"] is False
    assert {"invalid_record", "invalid_summary"} <= codes(result["diagnostics"])
    assert item(result)["classification"] == "blocked"


def test_proposed_with_blockers_stays_not_ready_and_all_excluded_is_distinct(tmp_path):
    goal(tmp_path, status="proposed", depends_on=["missing"])
    result = discovery.candidates(tmp_path)
    assert item(result)["classification"] == "not_ready"
    assert item(result)["eligible"] is False
    assert result["counts"]["not_ready"] == 1
    assert result["counts"]["blocked"] == 0
    boss.withdraw(tmp_path, "goal")
    result = discovery.candidates(tmp_path)
    assert result["items"] == []
    assert result["counts"]["total_live"] == result["counts"]["excluded"] == 1
    assert result["counts"]["pool"] == 0
    assert result["healthy"] is False
