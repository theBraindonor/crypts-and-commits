import sqlite3
from pathlib import Path

import frontmatter
import pytest
from cac.core import (
    boss,
    boss_candidates,
    campaign,
    config,
    coupling,
    encounter,
    frontmatter_utils,
    search_index,
    world,
)
from cac.core.paths import search_index_db_path
from cac.core.recovery import RecoveryError


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)


def available(root, name="b001-goal"):
    path = boss.create_boss(root, name, "## Goal\n\n[tool.ruff] café", "Summary")
    boss.make_available(root, name)
    # Keep unusual valid raw body whitespace that parsed frontmatter would normalize.
    path.write_bytes(path.read_bytes() + b"\r\n\r\n  \t\r\n")
    return path


def files(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*.md")}


def rows(root):
    path = search_index_db_path(root)
    if not path.exists():
        return None
    with sqlite3.connect(path) as connection:
        return sorted(
            connection.execute(
                f"SELECT object_type,campaign,name,status,updated_on,archived,body FROM {config.SEARCH_INDEX_FTS_TABLE}"
            ).fetchall()
        )


def set_metadata(path, **values):
    post = frontmatter.load(path)
    post.metadata.update(values)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")


def assign(root, campaign_name="c001-work"):
    return boss.assign_campaign(root, "b001-goal", campaign_name, "[tactical] campaign plan")


def test_assignment_defaults_content_and_retry_bytes(tmp_path):
    path = available(tmp_path)
    suffix = coupling._body_suffix(path.read_bytes())[1]
    result = assign(tmp_path)
    assert result["boss"] == "b001-goal" and result["campaign"] == "c001-work"
    assert result["status"] == "draft" and result["reused"] is False
    assert result["campaign_identity"]["short"] == "c001"
    metadata, body = campaign.read_metadata(tmp_path, "c001-work")
    assert metadata["boss"] == "b001-goal" and metadata["status"] == "draft"
    assert body == "[tactical] campaign plan"
    goal, _ = boss.read_metadata(tmp_path, "b001-goal")
    assert goal["campaign"] == "c001-work" and goal["status"] == "available"
    assert coupling._body_suffix(path.read_bytes())[1] == suffix
    before = files(tmp_path)
    assert boss.assign_campaign(tmp_path, "b001-goal", "c001-work", "Different retry body")["reused"] is True
    assert files(tmp_path) == before
    with pytest.raises(coupling.LinkError):
        assign(tmp_path, "c002-other")
    assert files(tmp_path) == before


def test_lifecycle_reactivation_and_archived_retry_preserve_boss_body(tmp_path):
    path = available(tmp_path)
    suffix = coupling._body_suffix(path.read_bytes())[1]
    assign(tmp_path)
    campaign.open_campaign(tmp_path, "c001-work")
    campaign.pause_campaign(tmp_path, "c001-work")
    assert boss.read_metadata(tmp_path, "b001-goal")[0]["status"] == "available"
    campaign.complete_campaign(tmp_path, "c001-work", "First completion")
    assert boss.read_metadata(tmp_path, "b001-goal")[0]["status"] == "vanquished"
    before = files(tmp_path)
    retry = assign(tmp_path)
    assert retry["status"] == "completed" and retry["reused"] is True
    assert files(tmp_path) == before
    campaign.reactivate_campaign(tmp_path, "c001-work", "PR feedback")
    before = files(tmp_path)
    with pytest.raises(campaign.CampaignNotMutableError, match="recorded Log"):
        campaign.update_campaign(tmp_path, "c001-work", "Erase history")
    assert files(tmp_path) == before
    campaign.update_campaign(
        tmp_path, "c001-work", campaign.read_campaign(tmp_path, "c001-work").body + "\n\nReview fix"
    )
    goal = boss.read_metadata(tmp_path, "b001-goal")[0]
    assert goal["status"] == "available" and goal["campaign"] == "c001-work"
    campaign.complete_campaign(tmp_path, "c001-work", "Second completion")
    text = campaign.read_campaign(tmp_path, "c001-work").body
    assert all(value in text for value in ("First completion", "PR feedback", "Review fix", "Second completion"))
    campaign.archive_campaign(tmp_path, "c001-work")
    assert boss.read_metadata(tmp_path, "b001-goal")[0]["archived"] is True
    assert coupling._body_suffix(boss.boss_path(tmp_path, "b001-goal").read_bytes())[1] == suffix
    before = files(tmp_path)
    assert assign(tmp_path)["status"] == "completed"
    assert files(tmp_path) == before
    with pytest.raises(campaign.CampaignNotMutableError):
        campaign.reactivate_campaign(tmp_path, "c001-work", "No restoration")


@pytest.mark.parametrize("later", ["available", "withdrawn", "archived", "reassigned", "vanquished"])
def test_abandoned_history_never_controls_released_boss(tmp_path, later):
    path = available(tmp_path)
    assign(tmp_path)
    campaign.abandon_campaign(tmp_path, "c001-work", "Cancelled")
    assert "campaign" not in boss.read_metadata(tmp_path, "b001-goal")[0]
    assert campaign.read_campaign(tmp_path, "c001-work").boss == "b001-goal"
    assert coupling.inspection(tmp_path, "c001-work")["kind"] == "historical"
    if later in ("withdrawn", "archived"):
        boss.withdraw(tmp_path, "b001-goal")
        if later == "archived":
            boss.archive_boss(tmp_path, "b001-goal")
    elif later in ("reassigned", "vanquished"):
        assign(tmp_path, "c002-new")
        if later == "vanquished":
            campaign.open_campaign(tmp_path, "c002-new")
            campaign.complete_campaign(tmp_path, "c002-new", "Done")
    path = boss.boss_path(tmp_path, "b001-goal")
    before = path.read_bytes()
    campaign.archive_campaign(tmp_path, "c001-work")
    assert path.read_bytes() == before
    with pytest.raises(coupling.CampaignLinkedError):
        campaign.delete_campaign(tmp_path, "c001-work")
    with pytest.raises((coupling.LinkError, boss.BossError)):
        assign(tmp_path, "c001-work")
    assert path.read_bytes() == before


@pytest.mark.parametrize("status", ["proposed", "withdrawn", "vanquished"])
def test_new_assignment_rejects_nonavailable_and_unsatisfied(tmp_path, status):
    path = available(tmp_path)
    set_metadata(path, status=status)
    before = files(tmp_path)
    with pytest.raises(boss.BossError):
        assign(tmp_path)
    assert files(tmp_path) == before


def test_prerequisites_orphans_and_budget_preflight(tmp_path, monkeypatch):
    available(tmp_path)
    available(tmp_path, "b002-prerequisite")
    boss.assign_dependency(tmp_path, "b001-goal", "b002-prerequisite")
    before = files(tmp_path)
    with pytest.raises(coupling.LinkError, match="eligible"):
        assign(tmp_path)
    assert files(tmp_path) == before
    set_metadata(boss.boss_path(tmp_path, "b002-prerequisite"), status="vanquished")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 10)
    before = files(tmp_path)
    with pytest.raises(coupling.LinkError, match="budget"):
        assign(tmp_path)
    assert files(tmp_path) == before
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 20000)
    orphan = campaign.create_campaign(tmp_path, "c999-orphan", "Orphan")
    set_metadata(orphan, boss="b001-goal")
    assert boss_candidates.assess(tmp_path, "b001-goal")["eligible"] is False
    with pytest.raises(coupling.LinkError, match="eligible"):
        assign(tmp_path)
    assert coupling.inspection(tmp_path, "c999-orphan")["kind"] == "invalid"


def test_reverse_claim_and_missing_current_campaign(tmp_path):
    available(tmp_path)
    path = available(tmp_path, "b002-other")
    set_metadata(path, campaign="c001-work")
    before = files(tmp_path)
    with pytest.raises(coupling.LinkError, match="claimed"):
        assign(tmp_path)
    assert files(tmp_path) == before
    set_metadata(boss.boss_path(tmp_path, "b001-goal"), campaign="missing")
    with pytest.raises(coupling.LinkError):
        assign(tmp_path, "missing")


@pytest.mark.parametrize("action", ["assignment", "complete", "abandon", "reactivate", "archive"])
@pytest.mark.parametrize("built_index", [False, True])
def test_second_record_failure_restores_files_and_logical_index(tmp_path, monkeypatch, action, built_index):
    available(tmp_path)
    if action != "assignment":
        assign(tmp_path)
        if action in ("complete", "reactivate", "archive"):
            campaign.open_campaign(tmp_path, "c001-work")
        if action in ("reactivate", "archive"):
            campaign.complete_campaign(tmp_path, "c001-work", "Done")
    if built_index:
        search_index.rebuild_index(tmp_path)
    before, old_rows = files(tmp_path), rows(tmp_path)
    original = coupling._write_boss

    def fail_after(*args, **kwargs):
        original(*args, **kwargs)
        raise OSError("Boss persistence failed after writing")

    monkeypatch.setattr(coupling, "_write_boss", fail_after)
    operation = {
        "assignment": lambda: assign(tmp_path),
        "complete": lambda: campaign.complete_campaign(tmp_path, "c001-work", "Done"),
        "abandon": lambda: campaign.abandon_campaign(tmp_path, "c001-work", "Cancelled"),
        "reactivate": lambda: campaign.reactivate_campaign(tmp_path, "c001-work", "Feedback"),
        "archive": lambda: campaign.archive_campaign(tmp_path, "c001-work"),
    }[action]
    with pytest.raises(OSError):
        operation()
    assert files(tmp_path) == before
    assert rows(tmp_path) == old_rows


@pytest.mark.parametrize("failed_record", ["encounter", "campaign", "boss"])
def test_archive_failure_restores_whole_encounter_cohort(tmp_path, monkeypatch, failed_record):
    available(tmp_path)
    assign(tmp_path)
    for name in ("e001-first", "e002-second"):
        encounter.create_encounter(tmp_path, "c001-work", name, "Body")
        encounter.abandon_encounter(tmp_path, "c001-work", name, "Not needed")
    campaign.open_campaign(tmp_path, "c001-work")
    campaign.complete_campaign(tmp_path, "c001-work", "Done")
    search_index.rebuild_index(tmp_path)
    before, old_rows = files(tmp_path), rows(tmp_path)
    original = Path.unlink
    source = {
        "encounter": encounter.encounter_path(tmp_path, "c001-work", "e002-second"),
        "campaign": campaign.campaign_path(tmp_path, "c001-work"),
        "boss": boss.boss_path(tmp_path, "b001-goal"),
    }[failed_record]

    def fail_unlink(path, *args, **kwargs):
        if path == source:
            raise OSError("Second encounter unlink failed")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_unlink)
    with pytest.raises(OSError):
        campaign.archive_campaign(tmp_path, "c001-work")
    assert files(tmp_path) == before and rows(tmp_path) == old_rows


def test_index_sync_failure_restores_assignment(tmp_path, monkeypatch):
    available(tmp_path)
    search_index.rebuild_index(tmp_path)
    before, old_rows = files(tmp_path), rows(tmp_path)
    original = search_index.sync_write

    def fail_sync(*args):
        original(*args)
        raise sqlite3.OperationalError("Index write failed")

    monkeypatch.setattr(search_index, "sync_write", fail_sync)
    with pytest.raises(sqlite3.OperationalError):
        assign(tmp_path)
    assert files(tmp_path) == before and rows(tmp_path) == old_rows


def test_failed_rollback_reports_residual_records(tmp_path, monkeypatch):
    path = available(tmp_path)
    original_boss = coupling._write_boss
    original_bytes = Path.write_bytes
    writing = False

    def fail_boss(*args, **kwargs):
        nonlocal writing
        original_boss(*args, **kwargs)
        writing = True
        raise OSError("Operation failed")

    def fail_restore(target, data):
        if target == path and writing:
            raise OSError("Restore denied")
        return original_bytes(target, data)

    monkeypatch.setattr(coupling, "_write_boss", fail_boss)
    monkeypatch.setattr(Path, "write_bytes", fail_restore)
    with pytest.raises(RecoveryError, match="recovery incomplete") as error:
        assign(tmp_path)
    assert "b001-goal.md" in str(error.value)
    assert not campaign.exists(tmp_path, "c001-work")


def test_bossless_reactivation_and_open_guard(tmp_path):
    campaign.create_campaign(tmp_path, "legacy", "Body")
    campaign.open_campaign(tmp_path, "legacy")
    campaign.complete_campaign(tmp_path, "legacy", "First")
    with pytest.raises(campaign.CampaignMessageRequiredError):
        campaign.reactivate_campaign(tmp_path, "legacy", " ")
    campaign.create_campaign(tmp_path, "other", "Other")
    campaign.open_campaign(tmp_path, "other")
    with pytest.raises(campaign.AnotherCampaignOpenError):
        campaign.reactivate_campaign(tmp_path, "legacy", "Feedback")
    campaign.pause_campaign(tmp_path, "other")
    campaign.reactivate_campaign(tmp_path, "legacy", "Feedback")
    assert "First" in campaign.read_campaign(tmp_path, "legacy").body
    assert campaign.read_campaign(tmp_path, "legacy").boss is None


@pytest.mark.parametrize(
    "defect",
    [
        "reverse",
        "different_boss",
        "missing_boss",
        "wrong_campaign",
        "duplicate_goal_claim",
        "duplicate_campaign_claim",
        "archive_mismatch",
    ],
)
def test_damaged_ownership_rejects_mutation_before_writes(tmp_path, defect):
    goal = available(tmp_path)
    assign(tmp_path)
    path = campaign.campaign_path(tmp_path, "c001-work")
    if defect == "reverse":
        post = frontmatter.load(path)
        post.metadata.pop("boss")
        path.write_text(frontmatter.dumps(post), encoding="utf-8")
    elif defect == "different_boss":
        available(tmp_path, "b002-other")
        set_metadata(path, boss="b002-other")
    elif defect == "missing_boss":
        set_metadata(path, boss="missing")
    elif defect == "wrong_campaign":
        set_metadata(goal, campaign="missing")
    elif defect == "duplicate_goal_claim":
        second = available(tmp_path, "b002-other")
        set_metadata(second, campaign="c001-work")
    elif defect == "duplicate_campaign_claim":
        second = campaign.create_campaign(tmp_path, "c002-second", "Competing")
        set_metadata(second, boss="b001-goal")
    else:
        set_metadata(goal, archived=True)
    before = files(tmp_path)
    with pytest.raises(coupling.LinkError):
        campaign.complete_campaign(tmp_path, "c001-work", "No")
    assert files(tmp_path) == before
    assert coupling.inspection(tmp_path, "c001-work")["kind"] == "invalid"


@pytest.mark.parametrize("record", ["campaign", "boss", "encounter"])
def test_archive_collision_preserves_every_record(tmp_path, record):
    available(tmp_path)
    assign(tmp_path)
    encounter.create_encounter(tmp_path, "c001-work", "e001-work", "Body")
    encounter.abandon_encounter(tmp_path, "c001-work", "e001-work", "Cancelled")
    campaign.open_campaign(tmp_path, "c001-work")
    campaign.complete_campaign(tmp_path, "c001-work", "Done")
    destination = {
        "campaign": campaign.archive_campaign_dir(tmp_path) / "c001-work.md",
        "boss": boss.boss_dir(tmp_path, archived=True) / "b001-goal.md",
        "encounter": encounter.archive_encounter_dir(tmp_path, "c001-work") / "e001-work.md",
    }[record]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("Existing destination must survive", encoding="utf-8")
    before = files(tmp_path)
    with pytest.raises(coupling.LinkError):
        campaign.archive_campaign(tmp_path, "c001-work")
    assert files(tmp_path) == before


@pytest.mark.parametrize("state", ["draft", "open", "paused", "abandoned", "archived"])
def test_reactivation_state_guards_do_not_mutate(tmp_path, state):
    available(tmp_path)
    assign(tmp_path)
    if state in ("open", "paused", "archived"):
        campaign.open_campaign(tmp_path, "c001-work")
    if state == "paused":
        campaign.pause_campaign(tmp_path, "c001-work")
    elif state == "abandoned":
        campaign.abandon_campaign(tmp_path, "c001-work", "Cancelled")
    elif state == "archived":
        campaign.complete_campaign(tmp_path, "c001-work", "Done")
        campaign.archive_campaign(tmp_path, "c001-work")
    before = files(tmp_path)
    with pytest.raises((campaign.InvalidCampaignTransitionError, campaign.CampaignNotMutableError)):
        campaign.reactivate_campaign(tmp_path, "c001-work", "No")
    assert files(tmp_path) == before


def test_direct_create_cannot_reuse_archives_or_reverse_claims(tmp_path):
    available(tmp_path)
    assign(tmp_path)
    campaign.open_campaign(tmp_path, "c001-work")
    campaign.complete_campaign(tmp_path, "c001-work", "Done")
    campaign.archive_campaign(tmp_path, "c001-work")
    before = files(tmp_path)
    with pytest.raises(campaign.CampaignAlreadyExistsError):
        campaign.create_campaign(tmp_path, "c001-work", "Hijack")
    assert files(tmp_path) == before
    path = available(tmp_path, "b002-orphan")
    set_metadata(path, campaign="c999-orphan")
    before = files(tmp_path)
    with pytest.raises(coupling.LinkError, match="claimed"):
        campaign.create_campaign(tmp_path, "c999-orphan", "Hijack")
    assert files(tmp_path) == before


def test_retry_under_tiny_budget_is_read_only(tmp_path, monkeypatch):
    available(tmp_path)
    assign(tmp_path)
    before = files(tmp_path)
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 10)
    with pytest.raises(coupling.LinkError, match="budget"):
        assign(tmp_path)
    assert files(tmp_path) == before


@pytest.mark.parametrize("action", ["assignment", "completion"])
def test_audit_failure_cannot_leave_half_an_assignment_or_completion(tmp_path, monkeypatch, action):
    from cac.core.git_utils import GitIdentityError

    available(tmp_path)
    if action == "completion":
        assign(tmp_path)
        campaign.open_campaign(tmp_path, "c001-work")
    search_index.rebuild_index(tmp_path)
    before, old_rows = files(tmp_path), rows(tmp_path)
    original = frontmatter_utils.stamp_updated

    def fail_boss_audit(post, root):
        if post.get("name") == "b001-goal":
            raise GitIdentityError("Audit identity unavailable")
        return original(post, root)

    monkeypatch.setattr(frontmatter_utils, "stamp_updated", fail_boss_audit)
    with pytest.raises(GitIdentityError):
        if action == "assignment":
            assign(tmp_path)
        else:
            campaign.complete_campaign(tmp_path, "c001-work", "Done")
    assert files(tmp_path) == before and rows(tmp_path) == old_rows


def test_linked_open_encounter_guard_is_prewrite(tmp_path):
    available(tmp_path)
    assign(tmp_path)
    campaign.open_campaign(tmp_path, "c001-work")
    path = encounter.create_encounter(tmp_path, "c001-work", "e001-open", "Body")
    set_metadata(path, status="open")
    before = files(tmp_path)
    with pytest.raises(campaign.CampaignHasOpenEncountersError):
        campaign.complete_campaign(tmp_path, "c001-work", "No")
    assert files(tmp_path) == before
