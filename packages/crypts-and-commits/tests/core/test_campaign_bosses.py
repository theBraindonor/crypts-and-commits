import sqlite3

import frontmatter
import pytest
from cac.core import (
    boss,
    boss_candidates,
    campaign,
    config,
    coupling,
    index_snapshot,
    prime,
    references,
    rumor,
    search_index,
    world,
)
from cac.core.paths import search_index_db_path


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)
    for number in range(1, 5):
        name = f"b{number:03d}-goal"
        path = boss.create_boss(tmp_path, name, "[design] café 🐉", "Summary")
        boss.make_available(tmp_path, name)
        path.write_bytes(path.read_bytes() + b"\r\n\r\n \t\r\n")


def files(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*.md")}


def evidence(root):
    with sqlite3.connect(search_index_db_path(root)) as connection:
        return (
            connection.execute("SELECT * FROM sourcebook_fts ORDER BY object_type,campaign,name").fetchall(),
            connection.execute(f"SELECT * FROM {index_snapshot.TABLE} ORDER BY object_type,campaign,name").fetchall(),
        )


def create(root):
    return campaign.create_campaign(root, "c001-work", "Tactics", ["b002", "b001", "b003"])


def test_group_creation_aliases_ownership_and_frozen_design(tmp_path):
    suffixes = {
        name: coupling._body_suffix(boss.boss_path(tmp_path, name).read_bytes())[1]
        for name in boss.list_bosses(tmp_path)
    }
    search_index.rebuild_index(tmp_path)
    path = create(tmp_path)
    names = ["b001-goal", "b002-goal", "b003-goal"]
    assert campaign.read_campaign(tmp_path, "c001-work").bosses == names
    assert frontmatter.load(path)["bosses"] == names and "boss" not in frontmatter.load(path)
    assert coupling.Links(tmp_path).current("c001-work") == names
    for name in names:
        assert boss.read_metadata(tmp_path, name)[0]["campaign"] == "c001-work"
        assert name not in [entry["name"] for entry in boss_candidates.candidates(tmp_path)["items"]]
        assert coupling._body_suffix(boss.boss_path(tmp_path, name).read_bytes())[1] == suffixes[name]
        with pytest.raises(boss.BossError):
            boss.update_boss(tmp_path, name, "No", "No")
    assert boss_candidates.candidates(tmp_path)["healthy"]
    assert search_index.status(tmp_path)["freshness"] == "fresh"
    before = files(tmp_path)
    with pytest.raises(boss.BossError):
        campaign.create_campaign(tmp_path, "c002-conflict", "No", ["b002"])
    assert files(tmp_path) == before
    result = boss.assign_campaign(tmp_path, "b002-goal", "c001-work", "Must not replace")
    assert result["reused"] is True and files(tmp_path) == before
    with pytest.raises(campaign.CampaignAlreadyExistsError):
        create(tmp_path)


def test_draft_replacement_noop_release_and_log(tmp_path, identity):
    create(tmp_path)
    search_index.rebuild_index(tmp_path)
    before, prior = files(tmp_path), evidence(tmp_path)
    campaign.set_bosses(tmp_path, "c001-work", ["b003", "b002", "b001"], "Same selection")
    assert files(tmp_path) == before and evidence(tmp_path) == prior
    identity(user="Changed planner")
    campaign.set_bosses(tmp_path, "c001-work", ["b002", "b004"], "[reason] Narrow scope")
    assert campaign.read_campaign(tmp_path, "c001-work").bosses == ["b002-goal", "b004-goal"]
    for name in ("b001-goal", "b003-goal"):
        assert "campaign" not in boss.read_metadata(tmp_path, name)[0]
        assert boss_candidates.assess(tmp_path, name)["eligible"]
    assert (
        boss.boss_path(tmp_path, "b002-goal").read_bytes()
        == before[str(boss.boss_path(tmp_path, "b002-goal").relative_to(tmp_path))]
    )
    body = campaign.read_campaign(tmp_path, "c001-work").body
    assert "[reason] Narrow scope" in body and "Previous bosses:" in body and "New bosses:" in body
    assert body.count("### Bosses changed -") == 1
    with pytest.raises(campaign.CampaignNotMutableError, match="recorded Log"):
        campaign.update_campaign(tmp_path, "c001-work", "Erase log")
    campaign.set_bosses(tmp_path, "c001-work", [], "Clear selection")
    assert campaign.read_campaign(tmp_path, "c001-work").bosses == []
    assert all("campaign" not in boss.read_metadata(tmp_path, name)[0] for name in boss.list_bosses(tmp_path))
    assert search_index.status(tmp_path)["freshness"] == "fresh"


@pytest.mark.parametrize("legacy", [None, "b001-goal"])
def test_legacy_reads_and_noop_are_side_effect_free_then_write_normalizes(tmp_path, legacy):
    path = campaign.create_campaign(tmp_path, "legacy", "Legacy body")
    post = frontmatter.load(path)
    post.metadata.pop("bosses")
    if legacy:
        post["boss"] = legacy
        goal = boss.boss_path(tmp_path, legacy)
        record = frontmatter.load(goal)
        record["campaign"] = "legacy"
        goal.write_text(frontmatter.dumps(record), encoding="utf-8")
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    before = files(tmp_path)
    names = [legacy] if legacy else []
    assert campaign.read_campaign(tmp_path, "legacy").bosses == names
    assert campaign.read_metadata(tmp_path, "legacy")[0]["bosses"] == names
    campaign.set_bosses(tmp_path, "legacy", names, "No change")
    assert files(tmp_path) == before
    campaign.open_campaign(tmp_path, "legacy")
    assert frontmatter.load(path)["bosses"] == names and "boss" not in frontmatter.load(path)


@pytest.mark.parametrize("bad", [None, "b001-goal", [""], [1], ["b001", "b001-goal"], ["b999"], ["../bad"]])
def test_invalid_group_inputs_fail_before_writes(tmp_path, bad):
    before = files(tmp_path)
    # None is the supported create default; it is not an explicit replacement set.
    if bad is None:
        campaign.create_campaign(tmp_path, "c001-work", "Tactics")
        before = files(tmp_path)
        operation = lambda: campaign.set_bosses(tmp_path, "c001-work", bad, "No")
    else:
        operation = lambda: campaign.create_campaign(tmp_path, "c001-work", "Tactics", bad)
    with pytest.raises((ValueError, OSError)):
        operation()
    assert files(tmp_path) == before


@pytest.mark.parametrize(
    "metadata",
    [
        {"boss": "b001-goal", "bosses": ["b001-goal"]},
        {"bosses": None},
        {"bosses": ["b001-goal", "b001-goal"]},
        {"boss": ["b001-goal"]},
    ],
)
def test_malformed_storage_rejected_without_repair(tmp_path, metadata):
    path = campaign.create_campaign(tmp_path, "c001-work", "Tactics")
    post = frontmatter.load(path)
    post.metadata.pop("bosses")
    post.metadata.update(metadata)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    before = files(tmp_path)
    with pytest.raises(ValueError):
        campaign.read_campaign(tmp_path, "c001-work")
    with pytest.raises(ValueError):
        campaign.open_campaign(tmp_path, "c001-work")
    assert files(tmp_path) == before


@pytest.mark.parametrize("state", ["open", "paused", "completed", "abandoned", "archived", "reactivated"])
def test_membership_locks_after_draft(tmp_path, state):
    create(tmp_path)
    campaign.open_campaign(tmp_path, "c001-work")
    if state == "paused":
        campaign.pause_campaign(tmp_path, "c001-work")
    elif state == "abandoned":
        campaign.abandon_campaign(tmp_path, "c001-work", "Cancelled")
    elif state in ("completed", "archived", "reactivated"):
        campaign.complete_campaign(tmp_path, "c001-work", "Done")
        if state == "archived":
            campaign.archive_campaign(tmp_path, "c001-work")
        elif state == "reactivated":
            campaign.reactivate_campaign(tmp_path, "c001-work", "Review")
    before = files(tmp_path)
    with pytest.raises(campaign.CampaignNotMutableError):
        campaign.set_bosses(tmp_path, "c001-work", ["b004"], "Scope creep")
    assert files(tmp_path) == before


def test_group_prerequisites_cannot_be_bypassed(tmp_path):
    boss.assign_dependency(tmp_path, "b002-goal", "b001-goal")
    before = files(tmp_path)
    with pytest.raises(coupling.LinkError, match="prerequisites"):
        campaign.create_campaign(tmp_path, "c001-work", "No", ["b001", "b002"])
    assert files(tmp_path) == before


def test_group_completion_reactivation_archive_and_downstream_eligibility(tmp_path):
    boss.assign_dependency(tmp_path, "b004-goal", "b001-goal")
    boss.assign_dependency(tmp_path, "b004-goal", "b002-goal")
    rumor_path = rumor.create_rumor(tmp_path, "r001-discovery", "Discoveries", "Idea", "execution")
    rumor.promote(tmp_path, "r001-discovery", "b001-goal")
    rumor_bytes = rumor_path.read_bytes()
    create(tmp_path)
    designs = {
        name: coupling._body_suffix(boss.boss_path(tmp_path, name).read_bytes())[1]
        for name in boss.list_bosses(tmp_path)
    }
    search_index.rebuild_index(tmp_path)
    campaign.open_campaign(tmp_path, "c001-work")
    campaign.complete_campaign(tmp_path, "c001-work", "All goals achieved")
    assert all(boss.read_metadata(tmp_path, f"b{number:03d}-goal")[0]["status"] == "vanquished" for number in (1, 2, 3))
    assert boss_candidates.assess(tmp_path, "b004-goal")["eligible"]
    campaign.reactivate_campaign(tmp_path, "c001-work", "Review fixes")
    assert not boss_candidates.assess(tmp_path, "b004-goal")["eligible"]
    campaign.complete_campaign(tmp_path, "c001-work", "Done again")
    campaign.archive_campaign(tmp_path, "c001-work")
    for name in ("b001-goal", "b002-goal", "b003-goal"):
        assert boss.read_metadata(tmp_path, name)[0]["archived"] is True
        assert coupling._body_suffix(boss.boss_path(tmp_path, name).read_bytes())[1] == designs[name]
    # Campaign lifecycle and archival never touch rumors, including ones promoted to its bosses.
    assert rumor_path.read_bytes() == rumor_bytes
    assert search_index.status(tmp_path)["freshness"] == "fresh"
    with pytest.raises(coupling.CampaignLinkedError):
        campaign.delete_campaign(tmp_path, "c001-work")


def test_abandoned_history_never_controls_released_group(tmp_path):
    create(tmp_path)
    campaign.abandon_campaign(tmp_path, "c001-work", "Cancelled")
    campaign.create_campaign(tmp_path, "c002-retry", "New effort", ["b001", "b002"])
    boss.withdraw(tmp_path, "b003-goal")
    boss.archive_boss(tmp_path, "b003-goal")
    before = {
        name: boss.boss_path(tmp_path, name).read_bytes() for name in boss.list_bosses(tmp_path, include_archived=True)
    }
    campaign.archive_campaign(tmp_path, "c001-work")
    assert campaign.read_campaign(tmp_path, "c001-work").bosses == ["b001-goal", "b002-goal", "b003-goal"]
    assert {name: boss.boss_path(tmp_path, name).read_bytes() for name in before} == before


@pytest.mark.parametrize("phase", ["create", "replace", "complete", "abandon", "reactivate", "archive"])
@pytest.mark.parametrize("fail_at", [1, 2, 3])
def test_group_failure_rolls_back_all_records_rows_and_fingerprints(tmp_path, monkeypatch, phase, fail_at):
    if phase != "create":
        create(tmp_path)
    if phase in ("complete", "reactivate", "archive"):
        campaign.open_campaign(tmp_path, "c001-work")
    if phase in ("reactivate", "archive"):
        campaign.complete_campaign(tmp_path, "c001-work", "Done")
    search_index.rebuild_index(tmp_path)
    before, prior = files(tmp_path), evidence(tmp_path)
    original = coupling._write_boss
    calls = 0

    def fail(*args):
        nonlocal calls
        calls += 1
        original(*args)
        if calls == fail_at:
            raise OSError("injected member failure")

    monkeypatch.setattr(coupling, "_write_boss", fail)
    operation = {
        "create": lambda: create(tmp_path),
        "replace": lambda: campaign.set_bosses(tmp_path, "c001-work", ["b004"], "Replace goals"),
        "complete": lambda: campaign.complete_campaign(tmp_path, "c001-work", "Done"),
        "abandon": lambda: campaign.abandon_campaign(tmp_path, "c001-work", "Cancelled"),
        "reactivate": lambda: campaign.reactivate_campaign(tmp_path, "c001-work", "Review"),
        "archive": lambda: campaign.archive_campaign(tmp_path, "c001-work"),
    }[phase]
    with pytest.raises(OSError):
        operation()
    assert files(tmp_path) == before and evidence(tmp_path) == prior
    assert search_index.status(tmp_path)["freshness"] == "fresh"


def test_plural_prime_budgets_preserve_all_names_and_member_hydration(tmp_path, monkeypatch):
    create(tmp_path)
    campaign.open_campaign(tmp_path, "c001-work")
    for name in ("b001-goal", "b002-goal", "b003-goal"):
        path = boss.boss_path(tmp_path, name)
        post = frontmatter.load(path)
        post.content = "[large body] 🐉" * 1000
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 3000)
    payload = prime.present(prime.assemble_prime(tmp_path))
    assert payload["active_boss_names"] == ["b001-goal", "b002-goal", "b003-goal"]
    assert len(payload["active_bosses"]) == 3 and payload["active_boss_diagnostics"] == []
    assert "active_boss" not in payload
    assert len(references.encoded(payload)) <= 3000
    assert {entry["ref"]["name"] for entry in payload["truncations"] if entry["ref"]["tool"] == "boss_get"} == set(
        payload["active_boss_names"]
    )
    boss.boss_path(tmp_path, "b002-goal").unlink()
    payload = prime.present(prime.assemble_prime(tmp_path))
    assert "b002-goal" in payload["active_boss_names"]
    assert any(item["boss"] == "b002-goal" for item in payload["active_boss_diagnostics"])
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 100)
    with pytest.raises(ValueError, match="metadata/state"):
        prime.present(prime.assemble_prime(tmp_path))


@pytest.mark.parametrize("failure", ["campaign", "audit", "fingerprint", "unlink", "recovery", "replacement-last"])
def test_group_failure_boundaries_preserve_cohort_or_report_recovery(tmp_path, monkeypatch, failure):
    from pathlib import Path

    from cac.core import frontmatter_utils
    from cac.core.recovery import RecoveryError

    create(tmp_path)
    if failure not in ("campaign", "replacement-last"):
        campaign.open_campaign(tmp_path, "c001-work")
    if failure == "unlink":
        campaign.complete_campaign(tmp_path, "c001-work", "Done")
    search_index.rebuild_index(tmp_path)
    before, prior = files(tmp_path), evidence(tmp_path)
    if failure == "audit":
        original = frontmatter_utils.stamp_updated

        def fail_stamp(post, root):
            if post.get("name") == "b002-goal":
                raise ValueError("Audit failed")
            return original(post, root)

        monkeypatch.setattr(frontmatter_utils, "stamp_updated", fail_stamp)
    elif failure == "campaign":
        original = frontmatter_utils.write_post

        def fail_campaign(*args):
            original(*args)
            raise OSError("After campaign persistence")

        monkeypatch.setattr(frontmatter_utils, "write_post", fail_campaign)
    elif failure == "unlink":
        original = Path.unlink
        target = boss.boss_path(tmp_path, "b002-goal")

        def fail_unlink(path, *args, **kwargs):
            if path == target:
                raise OSError("Middle boss unlink failed")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", fail_unlink)
    else:
        original = coupling._write_boss if failure == "replacement-last" else index_snapshot.sync
        count = 0

        def fail_late(*args, **kwargs):
            nonlocal count
            original(*args, **kwargs)
            count += 1
            if count == (4 if failure == "replacement-last" else 3):
                raise sqlite3.OperationalError("Later member index/write failed")

        monkeypatch.setattr(
            coupling if failure == "replacement-last" else index_snapshot,
            "_write_boss" if failure == "replacement-last" else "sync",
            fail_late,
        )
        if failure == "recovery":

            def fail_restore(*args):
                raise sqlite3.OperationalError("Recovery failed")

            monkeypatch.setattr(index_snapshot, "restore", fail_restore)
    operation = (
        (lambda: campaign.set_bosses(tmp_path, "c001-work", ["b004"], "Replace"))
        if failure in ("campaign", "replacement-last")
        else (
            (lambda: campaign.archive_campaign(tmp_path, "c001-work"))
            if failure == "unlink"
            else (lambda: campaign.complete_campaign(tmp_path, "c001-work", "Done"))
        )
    )
    with pytest.raises(RecoveryError if failure == "recovery" else (OSError, ValueError, sqlite3.Error)) as caught:
        operation()
    assert files(tmp_path) == before
    if failure == "recovery":
        assert "recovery incomplete" in str(caught.value)
    else:
        assert evidence(tmp_path) == prior


def test_unrelated_stale_source_remains_stale_after_group_mutation(tmp_path):
    create(tmp_path)
    search_index.rebuild_index(tmp_path)
    path = world.world_path(tmp_path)
    path.write_bytes(path.read_bytes() + b"\nExternal change")
    campaign.set_bosses(tmp_path, "c001-work", ["b001", "b004"], "Changed goals")
    assert search_index.status(tmp_path)["freshness"] == "stale"
    with pytest.raises(search_index.StaleIndexError):
        search_index.search(tmp_path, "Summary")
