import os
import sqlite3
from pathlib import Path

import pytest
from cac.core import boss, campaign, coupling, encounter, index_snapshot, lore, rumors, search_index, world
from cac.core.paths import search_index_db_path


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c001-work", "Tactical notes")


def assert_fresh(root):
    assert search_index.status(root)["freshness"] == "fresh"
    search_index.search(root, "nevermatches")


def snapshot(root):
    with sqlite3.connect(search_index_db_path(root)) as connection:
        return connection.execute(f"SELECT * FROM {index_snapshot.TABLE} ORDER BY object_type,campaign,name").fetchall()


@pytest.mark.parametrize("change", ["edit", "add", "delete", "rename", "archive", "metadata"])
def test_external_snapshot_changes_and_switch_back(tmp_path, change):
    path = campaign.campaign_path(tmp_path, "c001-work")
    original = path.read_bytes()
    times = path.stat()
    search_index.rebuild_index(tmp_path)
    extra = path.with_name("c002-external.md")
    if change == "edit":
        path.write_bytes(original.replace(b"Tactical", b"External"))
        os.utime(path, ns=(times.st_atime_ns, times.st_mtime_ns))
        assert path.stat().st_size == len(original)
    elif change == "metadata":
        path.write_bytes(original.replace(b"draft", b"other"))
    elif change == "add":
        extra.write_bytes(original)
    elif change == "delete":
        path.unlink()
    elif change == "rename":
        path.rename(extra)
    else:
        extra = campaign.archive_campaign_dir(tmp_path) / path.name
        extra.parent.mkdir(parents=True)
        path.rename(extra)
    before = search_index_db_path(tmp_path).read_bytes()
    for query in ("Tactical", "nevermatches"):
        with pytest.raises(search_index.StaleIndexError, match="developer"):
            search_index.search(tmp_path, query)
    assert search_index.status(tmp_path)["freshness"] == "stale"
    assert search_index_db_path(tmp_path).read_bytes() == before
    if extra.exists():
        extra.unlink()
    path.write_bytes(original)
    assert_fresh(tmp_path)


def test_unrelated_cac_writes_cannot_bless_external_change(tmp_path):
    search_index.rebuild_index(tmp_path)
    path = campaign.campaign_path(tmp_path, "c001-work")
    path.write_bytes(path.read_bytes().replace(b"Tactical", b"External"))
    lore.create_lore(tmp_path, "new-lore", "Supported write", "Summary")
    with pytest.raises(search_index.StaleIndexError):
        search_index.search(tmp_path, "Supported")
    search_index.rebuild_index(tmp_path)
    assert search_index.search(tmp_path, "External")[0].name == "c001-work"
    assert search_index.search(tmp_path, "Supported")[0].name == "new-lore"


def test_rumors_and_unrelated_files_do_not_stale_snapshot(tmp_path):
    search_index.rebuild_index(tmp_path)
    before = snapshot(tmp_path)
    rumors.write(tmp_path, "b999-rumor", "c001")
    (tmp_path / "unrelated.md").write_text("new", encoding="utf-8")
    assert_fresh(tmp_path)
    assert snapshot(tmp_path) == before
    assert search_index.search(tmp_path, "b999-rumor", object_type="boss") == []


@pytest.mark.parametrize("defect", ["legacy", "format", "corrupt", "parse", "unreadable", "directory"])
def test_unverifiable_indexes_report_stale_without_read_side_effects(tmp_path, monkeypatch, defect):
    search_index.rebuild_index(tmp_path)
    path = campaign.campaign_path(tmp_path, "c001-work")
    if defect in ("legacy", "format"):
        with sqlite3.connect(search_index_db_path(tmp_path)) as connection:
            connection.execute(
                f"DROP TABLE {index_snapshot.META}"
                if defect == "legacy"
                else f"UPDATE {index_snapshot.META} SET version='unsupported'"
            )
    elif defect == "corrupt":
        search_index_db_path(tmp_path).write_bytes(b"Not SQLite")
    elif defect == "parse":
        path.write_text("---\nname: [\n---\n", encoding="utf-8")
    else:
        method = "read_bytes" if defect == "unreadable" else "iterdir"
        original = getattr(Path, method)
        target = path if defect == "unreadable" else path.parent

        def denied(self, *args, **kwargs):
            if self == target:
                raise PermissionError("[restricted] cannot read")
            return original(self, *args, **kwargs)

        monkeypatch.setattr(Path, method, denied)
    before = search_index_db_path(tmp_path).read_bytes()
    with pytest.raises(search_index.StaleIndexError):
        search_index.search(tmp_path, "Tactical")
    assert search_index.status(tmp_path)["freshness"] == "stale"
    assert search_index_db_path(tmp_path).read_bytes() == before


def test_missing_index_reads_create_nothing(tmp_path):
    assert search_index.search(tmp_path, "Tactical") is None
    assert search_index.status(tmp_path)["freshness"] == "missing"
    assert not search_index_db_path(tmp_path).exists()


def test_legacy_incremental_write_does_not_upgrade_snapshot(tmp_path):
    search_index.rebuild_index(tmp_path)
    with sqlite3.connect(search_index_db_path(tmp_path)) as connection:
        connection.execute(f"DROP TABLE {index_snapshot.META}")
    lore.create_lore(tmp_path, "new", "newbody", "Summary")
    assert search_index.status(tmp_path)["freshness"] == "stale"
    search_index.rebuild_index(tmp_path)
    assert_fresh(tmp_path)


def test_boss_summary_lifecycle_dependency_and_archive_sync(tmp_path):
    search_index.rebuild_index(tmp_path)
    boss.create_boss(tmp_path, "legacy-goal", "Body", "uniquesummary")
    assert search_index.search(tmp_path, "uniquesummary", object_type="boss")[0].name == "legacy-goal"
    boss.update_boss(tmp_path, "legacy-goal", "Revised", "updatedsummary")
    assert search_index.search(tmp_path, "uniquesummary") == []
    assert search_index.search(tmp_path, "updatedsummary")[0].status == "proposed"
    boss.create_boss(tmp_path, "b002-other", "Other", "Other")
    boss.assign_dependency(tmp_path, "legacy-goal", "b002-other")
    assert_fresh(tmp_path)
    boss.unassign_dependency(tmp_path, "legacy-goal", "b002-other")
    boss.make_available(tmp_path, "legacy-goal")
    assert search_index.search(tmp_path, "updatedsummary")[0].status == "available"
    boss.withdraw(tmp_path, "legacy-goal")
    assert search_index.search(tmp_path, "updatedsummary")[0].status == "withdrawn"
    boss.archive_boss(tmp_path, "legacy-goal")
    assert_fresh(tmp_path)
    assert search_index.search(tmp_path, "updatedsummary") == []
    result = search_index.search(tmp_path, "updatedsummary", include_archived=True)[0]
    assert result.archived and result.status == "withdrawn"


@pytest.mark.parametrize("abandon", [False, True])
def test_coupled_lifecycle_and_encounter_archival_remain_fresh(tmp_path, abandon):
    boss.create_boss(tmp_path, "b001-goal", "Bossbody", "Summary")
    boss.make_available(tmp_path, "b001-goal")
    search_index.rebuild_index(tmp_path)
    boss.assign_campaign(tmp_path, "b001-goal", "c002-linked", "Tactics")
    assert_fresh(tmp_path)
    encounter.create_encounter(tmp_path, "c002-linked", "e001-work", "Encounterbody")
    encounter.abandon_encounter(tmp_path, "c002-linked", "e001-work", "Done")
    campaign.open_campaign(tmp_path, "c002-linked")
    if abandon:
        campaign.abandon_campaign(tmp_path, "c002-linked", "Cancelled")
        assert_fresh(tmp_path)
    else:
        campaign.complete_campaign(tmp_path, "c002-linked", "Done")
        assert search_index.search(tmp_path, "Bossbody")[0].status == "vanquished"
        assert_fresh(tmp_path)
        campaign.reactivate_campaign(tmp_path, "c002-linked", "Review")
        assert_fresh(tmp_path)
        campaign.complete_campaign(tmp_path, "c002-linked", "Done")
    campaign.archive_campaign(tmp_path, "c002-linked")
    assert_fresh(tmp_path)
    assert search_index.search(tmp_path, "Encounterbody") == []
    assert search_index.search(tmp_path, "Encounterbody", include_archived=True)[0].archived


@pytest.mark.parametrize("action", ["assignment", "complete", "abandon", "reactivate", "archive"])
def test_failure_restores_fingerprints_and_rows(tmp_path, monkeypatch, action):
    boss.create_boss(tmp_path, "b001-goal", "Body", "Summary")
    boss.make_available(tmp_path, "b001-goal")
    if action != "assignment":
        boss.assign_campaign(tmp_path, "b001-goal", "c002-linked", "Tactics")
        campaign.open_campaign(tmp_path, "c002-linked")
        if action in ("reactivate", "archive"):
            campaign.complete_campaign(tmp_path, "c002-linked", "Done")
    search_index.rebuild_index(tmp_path)
    before = snapshot(tmp_path)
    original = coupling._write_boss

    def failed(*args):
        original(*args)
        raise OSError("after committed boss row/fingerprint")

    monkeypatch.setattr(coupling, "_write_boss", failed)
    operation = {
        "assignment": lambda: boss.assign_campaign(tmp_path, "b001-goal", "c002-linked", "Tactics"),
        "complete": lambda: campaign.complete_campaign(tmp_path, "c002-linked", "Done"),
        "abandon": lambda: campaign.abandon_campaign(tmp_path, "c002-linked", "Cancelled"),
        "reactivate": lambda: campaign.reactivate_campaign(tmp_path, "c002-linked", "Review"),
        "archive": lambda: campaign.archive_campaign(tmp_path, "c002-linked"),
    }[action]
    with pytest.raises(OSError):
        operation()
    assert snapshot(tmp_path) == before
    assert_fresh(tmp_path)


def test_failed_rebuild_keeps_prior_snapshot_transaction(tmp_path, monkeypatch):
    search_index.rebuild_index(tmp_path)
    before = snapshot(tmp_path)
    original = index_snapshot.initialize

    def failed(*args):
        original(*args)
        raise sqlite3.OperationalError("manifest write failed")

    monkeypatch.setattr(index_snapshot, "initialize", failed)
    with pytest.raises(sqlite3.OperationalError):
        search_index.rebuild_index(tmp_path)
    assert snapshot(tmp_path) == before
    assert_fresh(tmp_path)


def test_rebuild_retains_orphan_encounters(tmp_path):
    encounter.create_encounter(tmp_path, "c001-work", "e001-orphan", "Orphanbody")
    campaign.delete_campaign(tmp_path, "c001-work")
    search_index.rebuild_index(tmp_path)
    assert_fresh(tmp_path)
    assert search_index.search(tmp_path, "Orphanbody")[0].name == "e001-orphan"


@pytest.mark.parametrize("failure", ["snapshot-sync", "archive-unlink", "recovery"])
def test_index_failures_restore_original_evidence_or_report_failed_recovery(tmp_path, monkeypatch, failure):
    from cac.core.recovery import RecoveryError

    boss.create_boss(tmp_path, "b001-goal", "Originalbody", "Summary")
    boss.make_available(tmp_path, "b001-goal")
    boss.assign_campaign(tmp_path, "b001-goal", "c002-linked", "Tactics")
    campaign.open_campaign(tmp_path, "c002-linked")
    if failure == "archive-unlink":
        campaign.complete_campaign(tmp_path, "c002-linked", "Done")
    search_index.rebuild_index(tmp_path)
    before = snapshot(tmp_path)
    original = index_snapshot.sync

    def fail_sync(*args, **kwargs):
        original(*args, **kwargs)
        raise sqlite3.OperationalError("fingerprint persistence failed")

    if failure == "archive-unlink":
        original_unlink = Path.unlink
        target = boss.boss_path(tmp_path, "b001-goal")

        def denied(path, *args, **kwargs):
            if path == target:
                raise PermissionError("unlink denied")
            return original_unlink(path, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", denied)
    else:
        monkeypatch.setattr(index_snapshot, "sync", fail_sync)
    if failure == "recovery":

        def failed_restore(*args):
            raise sqlite3.OperationalError("snapshot recovery failed")

        monkeypatch.setattr(index_snapshot, "restore", failed_restore)
    operation = campaign.archive_campaign if failure == "archive-unlink" else campaign.complete_campaign
    args = (tmp_path, "c002-linked") + (() if failure == "archive-unlink" else ("Done",))
    with pytest.raises(RecoveryError if failure == "recovery" else (OSError, sqlite3.Error)) as caught:
        operation(*args)
    if failure == "recovery":
        assert "recovery incomplete" in str(caught.value)
    else:
        assert snapshot(tmp_path) == before
        assert_fresh(tmp_path)


def test_standalone_boss_archive_failure_restores_index_and_snapshot(tmp_path, monkeypatch):
    boss.create_boss(tmp_path, "b001-goal", "Originalbody", "Summary")
    boss.withdraw(tmp_path, "b001-goal")
    search_index.rebuild_index(tmp_path)
    before = snapshot(tmp_path)
    original = Path.unlink
    target = boss.boss_path(tmp_path, "b001-goal")

    def denied(path, *args, **kwargs):
        if path == target:
            raise PermissionError("unlink denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", denied)
    with pytest.raises(PermissionError):
        boss.archive_boss(tmp_path, "b001-goal")
    assert snapshot(tmp_path) == before
    assert_fresh(tmp_path)
    assert search_index.search(tmp_path, "Originalbody")[0].archived is False
