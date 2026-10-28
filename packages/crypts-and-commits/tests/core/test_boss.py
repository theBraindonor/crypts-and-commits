from datetime import UTC, datetime
from pathlib import Path

import frontmatter
import pytest
from cac.core import boss, config, frontmatter_utils, git_utils, search_index, world


@pytest.fixture(autouse=True)
def bootstrapped(tmp_path):
    world.initialize_world(tmp_path)


def create(root, name="goal"):
    return boss.create_boss(root, name, "[tool.ruff]\n\nA goal.", "A summary.")


def fixture_metadata(root, name, **values):
    path = boss.boss_path(root, name)
    post = frontmatter.load(path)
    post.metadata.update(values)
    path.write_text(frontmatter.dumps(post), encoding="utf-8")


def test_empty_collection_and_creation_defaults(tmp_path, legacy_world):
    before = legacy_world.read_bytes()
    assert boss.list_bosses(tmp_path) == []
    assert not boss.boss_dir(tmp_path).exists()
    path = create(tmp_path, "Unnumbered.goal")
    metadata, body = boss.read_metadata(tmp_path, "Unnumbered.goal")
    assert metadata == {
        "name": "Unnumbered.goal",
        "summary": "A summary.",
        "status": "proposed",
        "archived": False,
        "depends_on": [],
        "created_by": "John Hoff",
        "updated_by": "John Hoff",
        "created_on": "2026-07-23T18:04:12Z",
        "updated_on": "2026-07-23T18:04:12Z",
    }
    assert body == "[tool.ruff]\n\nA goal."
    assert path.is_file()
    assert legacy_world.read_bytes() == before
    assert config.SOURCEBOOK_SCHEMA_VERSION == 1
    assert all(
        heading in boss.template_body()
        for heading in ("Goal", "Rationale", "Success Criteria", "Design Notes", "Open Questions")
    )


@pytest.mark.parametrize("name", [".", "..", "../escape", "a/b", "a\\b", ""])
def test_invalid_names_do_not_create_storage(tmp_path, name):
    with pytest.raises(boss.BossError):
        create(tmp_path, name)
    assert not boss.boss_dir(tmp_path).exists()


def test_requires_bootstrapped_world(tmp_path):
    world.world_path(tmp_path).unlink()
    with pytest.raises(FileNotFoundError):
        boss.list_bosses(tmp_path)
    with pytest.raises(FileNotFoundError):
        create(tmp_path)


def test_available_updates_and_metadata_in_body_do_not_change_state(tmp_path):
    create(tmp_path)
    create(tmp_path, "prerequisite")
    boss.make_available(tmp_path, "goal")
    body = "---\nstatus: vanquished\ncampaign: bypass\ndepends_on: [unknown]\n---\n[bold]literal[/bold]"
    boss.update_boss(tmp_path, "goal", body, "[summary]")
    boss.assign_dependency(tmp_path, "goal", "prerequisite")
    metadata, stored = boss.read_metadata(tmp_path, "goal")
    assert metadata["status"] == "available"
    assert metadata["depends_on"] == ["prerequisite"]
    assert "campaign" not in metadata
    assert stored == body


@pytest.mark.parametrize("status", config.BOSS_STATUSES)
@pytest.mark.parametrize("linked", [False, True])
@pytest.mark.parametrize(
    "operation,allowed",
    [
        (boss.make_available, {"proposed"}),
        (boss.withdraw, {"proposed", "available"}),
        (boss.reactivate, {"withdrawn"}),
        (boss.archive_boss, {"withdrawn"}),
        (lambda r, n: boss.update_boss(r, n, "Changed", "Changed"), {"proposed", "available"}),
        (lambda r, n: boss.assign_dependency(r, n, "other"), {"proposed", "available"}),
    ],
)
def test_state_matrix(tmp_path, status, linked, operation, allowed):
    path = create(tmp_path)
    create(tmp_path, "other")
    fixture_metadata(tmp_path, "goal", status=status, **({"campaign": "campaign"} if linked else {}))
    before = path.read_bytes()
    if status in allowed and not linked:
        operation(tmp_path, "goal")
    else:
        with pytest.raises(boss.BossError):
            operation(tmp_path, "goal")
        assert path.read_bytes() == before


def test_lifecycle_preserves_body_and_audit_creation(tmp_path):
    create(tmp_path)
    initial, body = boss.read_metadata(tmp_path, "goal")
    for operation, status in [
        (boss.make_available, "available"),
        (boss.withdraw, "withdrawn"),
        (boss.reactivate, "proposed"),
    ]:
        operation(tmp_path, "goal")
        metadata, actual = boss.read_metadata(tmp_path, "goal")
        assert metadata["status"] == status
        assert metadata["created_on"] == initial["created_on"]
        assert actual == body


def test_archive_discovery_and_reserved_allocation(tmp_path):
    live = create(tmp_path)
    body = boss.read_metadata(tmp_path, "goal")[1]
    boss.withdraw(tmp_path, "goal")
    archived = boss.archive_boss(tmp_path, "goal")
    assert not live.exists()
    assert boss.boss_path(tmp_path, "goal") == archived
    assert boss.list_bosses(tmp_path) == []
    assert boss.list_bosses(tmp_path, include_archived=True) == ["goal"]
    metadata, stored = boss.read_metadata(tmp_path, "goal")
    assert stored == body
    assert metadata["archived"] is True
    assert metadata["status"] == "withdrawn"
    with pytest.raises(boss.BossAlreadyExistsError):
        create(tmp_path)
    for operation in (boss.make_available, boss.withdraw, boss.reactivate, boss.archive_boss):
        with pytest.raises(boss.BossError):
            operation(tmp_path, "goal")
    with pytest.raises(boss.BossError):
        boss.update_boss(tmp_path, "goal", "No", "No")


@pytest.mark.parametrize("failure", ["write", "unlink"])
def test_archive_failure_restores_exact_record(tmp_path, monkeypatch, failure):
    live = create(tmp_path)
    boss.withdraw(tmp_path, "goal")
    before = live.read_bytes()
    original_write = frontmatter_utils.write_post
    original_unlink = Path.unlink

    def fail_write(root, path, post):
        original_write(root, path, post)
        raise OSError("archive write failed after persistence")

    def fail_unlink(path, *args, **kwargs):
        if path == live:
            raise OSError("live unlink failed")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(frontmatter_utils, "write_post", fail_write if failure == "write" else original_write)
    monkeypatch.setattr(Path, "unlink", fail_unlink)
    with pytest.raises(OSError):
        boss.archive_boss(tmp_path, "goal")
    assert live.read_bytes() == before
    assert not (boss.boss_dir(tmp_path, archived=True) / "goal.md").exists()


def test_collisions_and_nested_directory_exclusion(tmp_path):
    live = create(tmp_path)
    nested = boss.boss_dir(tmp_path) / "notes"
    nested.mkdir()
    (nested / "b999-not-a-boss.md").write_text("Not a boss", encoding="utf-8")
    assert boss.list_bosses(tmp_path, include_archived=True) == ["goal"]
    archive = boss.boss_dir(tmp_path, archived=True)
    archive.mkdir(parents=True)
    (archive / live.name).write_bytes(live.read_bytes())
    before = live.read_bytes()
    for operation in (
        boss.list_bosses,
        lambda r: boss.read_metadata(r, "goal"),
        lambda r: boss.archive_boss(r, "goal"),
    ):
        with pytest.raises(boss.BossError, match="mbiguous"):
            operation(tmp_path)
    assert live.read_bytes() == before


@pytest.mark.parametrize("collision", ["collection-file", "record-directory"])
def test_namespace_collisions(tmp_path, collision):
    directory = boss.boss_dir(tmp_path)
    if collision == "collection-file":
        directory.write_text("not a directory", encoding="utf-8")
    else:
        directory.mkdir()
        (directory / "goal.md").mkdir()
    with pytest.raises(boss.BossError):
        create(tmp_path)


def test_diamond_and_cycle_detection(tmp_path):
    for name in ("a", "b", "c", "d"):
        create(tmp_path, name)
    for source, target in [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]:
        boss.assign_dependency(tmp_path, source, target)
    path = boss.boss_path(tmp_path, "d")
    before = path.read_bytes()
    for target in ("a", "d"):
        with pytest.raises(boss.BossError):
            boss.assign_dependency(tmp_path, "d", target)
        assert path.read_bytes() == before
    with pytest.raises(boss.BossError, match="duplicate"):
        boss.assign_dependency(tmp_path, "a", "b")
    boss.unassign_dependency(tmp_path, "a", "b")
    assert boss.read_metadata(tmp_path, "a")[0]["depends_on"] == ["c"]


def test_withdrawn_incoming_edges_retained_and_removable(tmp_path):
    create(tmp_path, "a")
    create(tmp_path, "b")
    create(tmp_path, "c")
    boss.assign_dependency(tmp_path, "a", "b")
    boss.withdraw(tmp_path, "b")
    assert boss.read_metadata(tmp_path, "a")[0]["depends_on"] == ["b"]
    for archived in (False, True):
        if archived:
            boss.archive_boss(tmp_path, "b")
        with pytest.raises(boss.BossError, match="withdrawn"):
            boss.assign_dependency(tmp_path, "c", "b")
    boss.unassign_dependency(tmp_path, "a", "b")
    assert boss.read_metadata(tmp_path, "a")[0]["depends_on"] == []


@pytest.mark.parametrize("damage", [None, "a", [42], ["b", "b"], ["missing"], ["b"], ["../escape"]])
def test_damaged_graph_rejected_before_writes(tmp_path, damage):
    path = create(tmp_path, "a")
    create(tmp_path, "b")
    create(tmp_path, "c")
    fixture_metadata(tmp_path, "b", depends_on=damage)
    before = path.read_bytes()
    with pytest.raises(boss.BossError):
        boss.assign_dependency(tmp_path, "a", "c")
    assert path.read_bytes() == before


def test_missing_target_edge_can_be_removed(tmp_path):
    create(tmp_path)
    fixture_metadata(tmp_path, "goal", depends_on=["missing"])
    boss.unassign_dependency(tmp_path, "goal", "missing")
    assert boss.read_metadata(tmp_path, "goal")[0]["depends_on"] == []


def test_cycle_edge_can_be_removed_but_unrelated_cycle_blocks_changes(tmp_path):
    for name in ("a", "b", "c", "d"):
        create(tmp_path, name)
    fixture_metadata(tmp_path, "a", depends_on=["b"])
    fixture_metadata(tmp_path, "b", depends_on=["a"])
    with pytest.raises(boss.BossError, match="cycle"):
        boss.assign_dependency(tmp_path, "c", "d")
    boss.unassign_dependency(tmp_path, "b", "a")
    boss.assign_dependency(tmp_path, "c", "d")


def test_archived_vanquished_prerequisite(tmp_path):
    create(tmp_path, "done")
    fixture_metadata(tmp_path, "done", status="vanquished", archived=True, campaign="old-campaign")
    live = boss.boss_dir(tmp_path) / "done.md"
    archived = boss.boss_dir(tmp_path, archived=True) / "done.md"
    archived.parent.mkdir(parents=True)
    live.rename(archived)
    create(tmp_path)
    boss.assign_dependency(tmp_path, "goal", "done")
    assert boss.read_metadata(tmp_path, "goal")[0]["depends_on"] == ["done"]


def test_summary_errors_leave_record_unchanged(tmp_path):
    with pytest.raises(frontmatter_utils.SummaryTooLongError):
        boss.create_boss(tmp_path, "goal", "Body", "x" * 501)
    assert not boss.boss_dir(tmp_path).exists()
    path = create(tmp_path)
    before = path.read_bytes()
    with pytest.raises(frontmatter_utils.SummaryTooLongError):
        boss.update_boss(tmp_path, "goal", "Changed", "x" * 501)
    assert path.read_bytes() == before


def test_audit_updates_and_identity_failure_are_prewrite(tmp_path, identity, monkeypatch):
    path = create(tmp_path)
    original = boss.read_metadata(tmp_path, "goal")[0]
    identity(user="Planner", when=datetime(2026, 10, 27, tzinfo=UTC))
    boss.make_available(tmp_path, "goal")
    updated = boss.read_metadata(tmp_path, "goal")[0]
    assert updated["created_by"] == original["created_by"]
    assert updated["created_on"] == original["created_on"]
    assert updated["updated_by"] == "Planner"
    assert updated["updated_on"] == "2026-10-27T00:00:00Z"
    before = path.read_bytes()

    def denied(root):
        raise git_utils.GitIdentityError("No identity")

    monkeypatch.setattr(git_utils, "current_git_user", denied)
    with pytest.raises(git_utils.GitIdentityError):
        boss.withdraw(tmp_path, "goal")
    assert path.read_bytes() == before


def test_boss_operations_do_not_create_or_change_search_index(tmp_path):
    create(tmp_path)
    assert search_index.index_counts(tmp_path) is None
    search_index.rebuild_index(tmp_path)
    before = search_index.index_counts(tmp_path)
    boss.update_boss(tmp_path, "goal", "Changed", "Changed")
    boss.withdraw(tmp_path, "goal")
    boss.archive_boss(tmp_path, "goal")
    assert search_index.index_counts(tmp_path) == before


def test_archived_dependency_mutations_and_missing_edge_leave_bytes_unchanged(tmp_path):
    create(tmp_path)
    create(tmp_path, "other")
    boss.assign_dependency(tmp_path, "goal", "other")
    with pytest.raises(boss.BossError, match="no dependency"):
        boss.unassign_dependency(tmp_path, "other", "goal")
    boss.withdraw(tmp_path, "goal")
    path = boss.archive_boss(tmp_path, "goal")
    before = path.read_bytes()
    for operation in (boss.assign_dependency, boss.unassign_dependency):
        with pytest.raises(boss.BossError):
            operation(tmp_path, "goal", "other")
        assert path.read_bytes() == before


def test_linked_record_path_is_rejected_before_read(tmp_path, monkeypatch):
    path = create(tmp_path)
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda p: p == path or original(p))
    with pytest.raises(boss.BossError, match="links"):
        boss.read_metadata(tmp_path, "goal")
