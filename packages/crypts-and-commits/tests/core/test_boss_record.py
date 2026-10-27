import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import frontmatter
import pytest
from cac.core import (
    boss,
    boss_candidates,
    boss_provenance,
    campaign,
    config,
    coupling,
    frontmatter_utils,
    index_snapshot,
    prime,
    references,
    search_index,
    world,
)
from cac.core.paths import search_index_db_path
from cac.core.recovery import RecoveryError


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)


def record(root, name="b001-old", progress="completed", **kwargs):
    return boss.record_boss(
        root, name, "[Goal] café 🐉", "Recordedsummary", progress, "roadmap.md#old", "Release evidence", **kwargs
    )


def files(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*.md")}


def evidence(root):
    with sqlite3.connect(search_index_db_path(root)) as connection:
        return (
            connection.execute("SELECT * FROM sourcebook_fts ORDER BY object_type,campaign,name").fetchall(),
            connection.execute(f"SELECT * FROM {index_snapshot.TABLE} ORDER BY object_type,campaign,name").fetchall(),
        )


def test_incremental_adoption_context_and_archive(tmp_path):
    search_index.rebuild_index(tmp_path)
    path = record(tmp_path, completed_on="2024-02-29")
    original, body = boss.read_metadata(tmp_path, "b001-old")
    assert original["status"] == "vanquished" and original.get("campaign") is None
    assert original["created_on"] == "2026-07-23T18:04:12Z"
    assert original["provenance"]["completed_on"] == "2024-02-29"
    record(tmp_path, "b002-next", "planned", depends_on=["b001"])
    record(tmp_path, "b003-underway", "in_progress")
    result = boss_candidates.candidates(tmp_path)
    assert result["healthy"] and result["counts"]["excluded"] == 1
    assert all(item["classification"] == "not_ready" for item in result["items"])
    next_goal = boss_candidates.assess(tmp_path, "b002-next")
    assert next_goal["prerequisites"][0]["completion_origin"] == "roadmap"
    assert next_goal["prerequisites"][0]["satisfied"]
    assert next_goal["roadmap"]["recorded_progress"] == "planned"
    assert next_goal["roadmap"]["source"] == "roadmap.md#old"
    assert campaign.list_campaigns(tmp_path) == []
    assert prime.present(prime.assemble_prime(tmp_path))["active_bosses"] == []
    path.write_bytes(path.read_bytes() + b"\r\n\r\n \t\r\n")
    suffix = coupling._body_suffix(path.read_bytes())[1]
    search_index.rebuild_index(tmp_path)
    archived = boss.archive_boss(tmp_path, "b001-old")
    assert not path.exists() and coupling._body_suffix(archived.read_bytes())[1] == suffix
    after, stored = boss.read_metadata(tmp_path, "b001-old")
    assert stored == body and after["archived"] and after["status"] == "vanquished"
    assert after["provenance"] == original["provenance"] and after["created_on"] == original["created_on"]
    assert references.Inventory(tmp_path).resolve("boss", "b001") == "b001-old"
    assert boss_candidates.assess(tmp_path, "b002-next")["prerequisites"][0]["satisfied"]
    boss.make_available(tmp_path, "b002-next")
    assert boss_candidates.assess(tmp_path, "b002-next")["eligible"]
    assert search_index.status(tmp_path)["freshness"] == "fresh"
    assert "b001-old" not in [hit.name for hit in search_index.search(tmp_path, "Recordedsummary")]
    assert "b001-old" in [hit.name for hit in search_index.search(tmp_path, "Recordedsummary", include_archived=True)]


def test_snapshot_survives_normal_cac_lifecycle(tmp_path):
    record(tmp_path, progress="in_progress")
    snapshot = boss.read_metadata(tmp_path, "b001-old")[0]["provenance"]
    boss.update_boss(tmp_path, "b001-old", "Refined", "Refined summary")
    boss.withdraw(tmp_path, "b001-old")
    boss.reactivate(tmp_path, "b001-old")
    boss.make_available(tmp_path, "b001-old")
    campaign.create_campaign(tmp_path, "c001-work", "Tactics", ["b001"])
    campaign.open_campaign(tmp_path, "c001-work")
    campaign.complete_campaign(tmp_path, "c001-work", "Done")
    campaign.reactivate_campaign(tmp_path, "c001-work", "Review")
    campaign.complete_campaign(tmp_path, "c001-work", "Done again")
    with pytest.raises(boss.BossError):
        boss.archive_boss(tmp_path, "b001-old")
    campaign.archive_campaign(tmp_path, "c001-work")
    assert boss.read_metadata(tmp_path, "b001-old")[0]["provenance"] == snapshot


@pytest.mark.parametrize(
    "operation",
    [
        boss.make_available,
        boss.withdraw,
        boss.reactivate,
        lambda root, name: boss.update_boss(root, name, "Altered", "Altered"),
        lambda root, name: boss.assign_dependency(root, name, "other"),
        lambda root, name: boss.assign_campaign(root, name, "c001-fake", "Fake"),
    ],
)
def test_external_completion_is_frozen(tmp_path, operation):
    record(tmp_path)
    boss.create_boss(tmp_path, "other", "Other", "Other")
    before = files(tmp_path)
    with pytest.raises(ValueError):
        operation(tmp_path, "b001-old")
    assert files(tmp_path) == before


@pytest.mark.parametrize(
    "overrides",
    [
        {"progress": "available"},
        {"progress": None},
        {"source": " "},
        {"source": []},
        {"message": "\t"},
        {"message": 1},
        {"completed_on": "2023-02-29"},
        {"completed_on": "9999-01-01"},
        {"completed_on": "2024-2-29"},
        {"completed_on": "2024-02-29T00:00:00Z"},
        {"completed_on": True},
        {"progress": "planned", "completed_on": "2024-02-29"},
        {"progress": "in_progress", "completed_on": "2024-02-29"},
        {"summary": "s" * 501},
        {"body": None},
        {"depends_on": "b002"},
    ],
)
def test_invalid_record_is_rejected_before_writes(tmp_path, overrides):
    args = {
        "name": "b001-old",
        "body": "Body",
        "summary": "Summary",
        "progress": "completed",
        "source": "Source",
        "message": "Evidence",
    }
    args.update(overrides)
    before = files(tmp_path)
    with pytest.raises(ValueError):
        boss.record_boss(tmp_path, **args)
    assert files(tmp_path) == before


@pytest.mark.parametrize("progress", ["planned", "in_progress", "completed"])
def test_collision_never_upserts_live_or_archived(tmp_path, progress):
    record(tmp_path)
    for archived in (False, True):
        before = files(tmp_path)
        with pytest.raises(boss.BossAlreadyExistsError):
            record(tmp_path, progress=progress)
        assert files(tmp_path) == before
        if not archived:
            boss.archive_boss(tmp_path, "b001-old")


@pytest.mark.parametrize("targets", [["b002", "b002-other"], ["missing"], ["b001-old"], [None]])
def test_dependency_errors_preflight(tmp_path, targets):
    boss.create_boss(tmp_path, "b002-other", "Other", "Other")
    before = files(tmp_path)
    with pytest.raises((ValueError, boss.BossNotFoundError)):
        record(tmp_path, depends_on=targets)
    assert files(tmp_path) == before


def test_ambiguous_withdrawn_and_damaged_dependencies(tmp_path):
    first = boss.create_boss(tmp_path, "b002-other", "Other", "Other")
    boss.create_boss(tmp_path, "b2-duplicate", "Other", "Other")
    with pytest.raises(references.AmbiguousReferenceError):
        record(tmp_path, depends_on=["b002"])
    boss.withdraw(tmp_path, "b002-other")
    with pytest.raises(ValueError, match="withdrawn"):
        record(tmp_path, depends_on=["b002-other"])
    boss.reactivate(tmp_path, "b002-other")
    post = frontmatter.load(first)
    post["depends_on"] = ["missing"]
    first.write_text(frontmatter.dumps(post), encoding="utf-8")
    with pytest.raises(ValueError, match="missing"):
        record(tmp_path)
    post["depends_on"] = ["b2-duplicate"]
    first.write_text(frontmatter.dumps(post), encoding="utf-8")
    second = boss.boss_path(tmp_path, "b2-duplicate")
    post = frontmatter.load(second)
    post["depends_on"] = ["b002-other"]
    second.write_text(frontmatter.dumps(post), encoding="utf-8")
    with pytest.raises(ValueError, match="cycle"):
        record(tmp_path)


def test_historical_completion_does_not_replay_prerequisite_readiness(tmp_path):
    boss.create_boss(tmp_path, "legacy", "Legacy", "Legacy")
    record(tmp_path, depends_on=["legacy"])
    record(tmp_path, "b002-next", "planned", depends_on=["b001"])
    assert boss_candidates.assess(tmp_path, "b002-next")["prerequisites"][0]["satisfied"]
    path = boss.boss_path(tmp_path, "legacy")
    post = frontmatter.load(path)
    post["depends_on"] = ["missing"]
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    assert not boss_candidates.assess(tmp_path, "b002-next")["prerequisites"][0]["satisfied"]


@pytest.mark.parametrize("broken", [None, {}, "roadmap", {"kind": "roadmap"}])
def test_invalid_provenance_cannot_be_trusted(tmp_path, broken):
    path = record(tmp_path)
    record(tmp_path, "b002-next", "planned", depends_on=["b001"])
    post = frontmatter.load(path)
    post["provenance"] = broken
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    before = files(tmp_path)
    with pytest.raises(ValueError, match="provenance"):
        boss.read_metadata(tmp_path, "b001-old")
    with pytest.raises(ValueError):
        boss.archive_boss(tmp_path, "b001-old")
    result = boss_candidates.assess(tmp_path, "b002-next")
    assert not result["prerequisites"][0]["satisfied"] and result["diagnostics"]
    assert files(tmp_path) == before


def test_legacy_reads_do_not_gain_provenance_or_archive_permission(tmp_path):
    path = boss.create_boss(tmp_path, "legacy", "Original", "Legacy")
    post = frontmatter.load(path)
    post["status"] = "vanquished"
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    before = files(tmp_path)
    assert "provenance" not in boss.read_metadata(tmp_path, "legacy")[0]
    with pytest.raises(boss.BossError):
        boss.archive_boss(tmp_path, "legacy")
    assert files(tmp_path) == before


@pytest.mark.parametrize("action", ["record", "archive"])
@pytest.mark.parametrize("failure", ["write", "sync", "fingerprint", "audit", "recovery"])
def test_failure_recovers_bytes_rows_and_fingerprints(tmp_path, monkeypatch, action, failure):
    if action == "archive":
        record(tmp_path)
    search_index.rebuild_index(tmp_path)
    before, prior = files(tmp_path), evidence(tmp_path)
    original = frontmatter_utils.write_post if action == "record" else coupling._write_boss
    sync = search_index.sync_write
    fingerprint = index_snapshot.sync

    def fail_write(*args):
        original(*args)
        raise OSError("after destination persistence")

    def fail_sync(*args):
        sync(*args)
        raise OSError("after index persistence")

    def fail_fingerprint(*args, **kwargs):
        fingerprint(*args, **kwargs)
        raise OSError("after fingerprint persistence")

    def denied(*args):
        raise OSError("audit unavailable")

    if failure in ("write", "recovery"):
        monkeypatch.setattr(
            frontmatter_utils if action == "record" else coupling,
            "write_post" if action == "record" else "_write_boss",
            fail_write,
        )
    elif failure == "sync":
        monkeypatch.setattr(search_index, "sync_write", fail_sync)
    elif failure == "fingerprint":
        monkeypatch.setattr(index_snapshot, "sync", fail_fingerprint)
    else:
        monkeypatch.setattr(frontmatter_utils, "stamp_created" if action == "record" else "stamp_updated", denied)
    if failure == "recovery":
        monkeypatch.setattr(index_snapshot, "restore", denied)
    with pytest.raises(RecoveryError if failure == "recovery" else OSError) as caught:
        record(tmp_path) if action == "record" else boss.archive_boss(tmp_path, "b001-old")
    if failure == "recovery":
        assert "recovery incomplete" in str(caught.value)
    else:
        assert files(tmp_path) == before and evidence(tmp_path) == prior
        assert search_index.status(tmp_path)["freshness"] == "fresh"


def test_unlink_failure_and_unrelated_drift_are_preserved(tmp_path, monkeypatch):
    path = record(tmp_path)
    search_index.rebuild_index(tmp_path)
    world_path = world.world_path(tmp_path)
    world_path.write_bytes(world_path.read_bytes() + b"\nExternal drift\n")
    before, prior = files(tmp_path), evidence(tmp_path)
    unlink = Path.unlink

    def denied(target, *args, **kwargs):
        if target == path:
            raise PermissionError("source unlink denied")
        return unlink(target, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", denied)
    with pytest.raises(PermissionError):
        boss.archive_boss(tmp_path, "b001-old")
    assert files(tmp_path) == before and evidence(tmp_path) == prior
    record(tmp_path, "b002-next", "planned")
    assert search_index.status(tmp_path)["freshness"] == "stale"


def test_budget_preflight_and_read_only_hydration(tmp_path, monkeypatch):
    path = record(tmp_path)
    metadata, body = boss.read_metadata(tmp_path, "b001-old")
    before = path.read_bytes()
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 1500)
    result = boss.budget_response(
        tmp_path, "b001-old", {"metadata": metadata, "body": ('"\\\n' * 2000), "summary": "S"}
    )
    assert len(references.encoded(result)) <= 1500
    assert result["metadata"] == metadata and "boss_get" in result["body"] and "TRUNCATED" in result["body"]
    assert path.read_bytes() == before
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 100)
    with pytest.raises(ValueError, match="before writes"):
        record(tmp_path, "b002-next")
    assert not (boss.boss_dir(tmp_path) / "b002-next.md").exists()
    with pytest.raises(ValueError, match="response budget"):
        boss.budget_response(tmp_path, "b001-old", {"metadata": metadata, "body": body})


def test_date_uses_utc_calendar_today(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz == UTC
            return cls(2026, 1, 1, 0, 0, tzinfo=UTC)

    monkeypatch.setattr(boss_provenance, "datetime", Clock)
    value = {
        "kind": "roadmap",
        "progress": "completed",
        "source": "Source",
        "message": "Evidence",
        "completed_on": "2026-01-01",
    }
    assert boss_provenance.validate(value) == value
    value["completed_on"] = "2026-01-02"
    with pytest.raises(ValueError, match="future"):
        boss_provenance.validate(value)
