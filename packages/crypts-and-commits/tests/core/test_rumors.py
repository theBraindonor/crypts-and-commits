import json

import pytest
from cac.core import boss, boss_candidates, budget, campaign, config, references, rumors, search_index, world


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c001-work", "Campaign")


@pytest.mark.parametrize("text", ["", "---\r\nstatus: invented\r\n---\r\n\r\n[tool.ruff] café 🐉\n\n", "  \n"])
def test_literal_documents_and_existence_contract(tmp_path, text):
    assert rumors.list_documents(tmp_path) == {"items": [], "next_cursor": None}
    assert not rumors._directory(tmp_path).exists()
    for operation in (rumors.get, rumors.delete):
        with pytest.raises(ValueError, match="do not exist"):
            operation(tmp_path, "c001")
    with pytest.raises(ValueError, match="do not exist"):
        rumors.write(tmp_path, text, "c001", update=True)
    result = rumors.write(tmp_path, text, "c001")
    assert result["identity"]["canonical"] == "c001-work"
    assert rumors._path(tmp_path, "c001-work").read_bytes() == text.encode()
    assert rumors.get(tmp_path, "c001-work")["body"] == text
    with pytest.raises(ValueError, match="already exist"):
        rumors.write(tmp_path, "overwrite", "c001")
    assert rumors.read_body(tmp_path, "c001") == text
    rumors.write(tmp_path, "", "c001", update=True)
    assert rumors.read_body(tmp_path, "c001") == ""
    rumors.delete(tmp_path, "c001")
    assert rumors.list_documents(tmp_path)["items"] == []


def test_active_fallback_independence_and_invalid_references(tmp_path):
    with pytest.raises(campaign.NoActiveCampaignError):
        rumors.write(tmp_path, "No active")
    campaign.open_campaign(tmp_path, "c001-work")
    rumors.write(tmp_path, "First")
    campaign.create_campaign(tmp_path, "c002-other", "Other")
    rumors.write(tmp_path, "Second", "c002")
    assert rumors.get(tmp_path)["body"] == "First"
    assert rumors.get(tmp_path, "c002")["body"] == "Second"
    before = rumors.read_body(tmp_path)
    for name in ("../escape", "missing", "c999", "b001"):
        with pytest.raises((ValueError, campaign.CampaignNotFoundError)):
            rumors.write(tmp_path, "bad", name, update=True)
    campaign.create_campaign(tmp_path, "c001-collision", "Collision")
    with pytest.raises(references.AmbiguousReferenceError):
        rumors.get(tmp_path, "c001")
    assert rumors.get(tmp_path, "c001-work")["body"] == before


@pytest.mark.parametrize("abandon", [False, True])
def test_coupled_lifecycle_and_archived_owner_editing(tmp_path, abandon):
    boss.create_boss(tmp_path, "b001-goal", "Goal", "Summary")
    boss.make_available(tmp_path, "b001-goal")
    boss.assign_campaign(tmp_path, "b001-goal", "c002-linked", "Tactics")
    text = "---\r\n[notes] 🐉\r\n\r\n"
    rumors.write(tmp_path, text, "c002")
    path = rumors._path(tmp_path, "c002-linked")
    campaign.open_campaign(tmp_path, "c002-linked")
    if abandon:
        campaign.abandon_campaign(tmp_path, "c002-linked", "Cancelled")
    else:
        campaign.complete_campaign(tmp_path, "c002-linked", "Done")
        assert path.read_bytes() == text.encode()
        rumors.write(tmp_path, text, "c002", update=True)
        campaign.reactivate_campaign(tmp_path, "c002-linked", "Review")
        assert path.read_bytes() == text.encode()
        campaign.complete_campaign(tmp_path, "c002-linked", "Done again")
    assert path.read_bytes() == text.encode()
    with pytest.raises(campaign.CampaignNotMutableError):
        campaign.update_campaign(tmp_path, "c002-linked", "Locked")
    campaign.archive_campaign(tmp_path, "c002-linked")
    assert path.read_bytes() == text.encode()
    assert rumors.get(tmp_path, "c002")["body"] == text
    assert "c002-linked" in [item["campaign"] for item in rumors.list_documents(tmp_path)["items"]]
    if not abandon:
        assert boss.read_metadata(tmp_path, "b001-goal")[0]["archived"] is True
        with pytest.raises(ValueError):
            boss.update_boss(tmp_path, "b001-goal", "No", "No")
    rumors.write(tmp_path, "Distilled", "c002", update=True)
    assert rumors.get(tmp_path, "c002")["body"] == "Distilled"
    rumors.delete(tmp_path, "c002")


def test_large_document_reconstruction_and_stale_cursor(tmp_path, monkeypatch):
    text = '🦉\r\n"\\[literal]\t' * 500
    rumors.write(tmp_path, text, "c001")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 600)
    chunks, cursor = [], None
    while True:
        result = rumors.get(tmp_path, "c001", cursor)
        assert len(references.encoded(result)) <= 600
        assert "disk" not in (result["notice"] or "")
        chunks.append(result["body"])
        cursor = result["next_cursor"]
        if cursor is None:
            break
        assert result["truncated"] and "TRUNCATED" in result["notice"]
    assert "".join(chunks) == text
    cursor = rumors.get(tmp_path, "c001")["next_cursor"]
    rumors.write(tmp_path, "changed", "c001", update=True)
    for bad in (cursor, "bad", "hash:-1", "hash:99999"):
        with pytest.raises(budget.InvalidCursorError):
            rumors.get(tmp_path, "c001", bad)
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 10)
    with pytest.raises(ValueError, match="budget"):
        rumors.write(tmp_path, "should not write", "c001", update=True)
    assert rumors.read_body(tmp_path, "c001") == "changed"


def test_list_pagination_orphans_and_invalid_cursors(tmp_path, monkeypatch):
    for number in range(1, 7):
        name = f"c{number:03d}-work"
        if number > 1:
            campaign.create_campaign(tmp_path, name, "Campaign")
        rumors.write(tmp_path, "Notes", name)
    campaign.delete_campaign(tmp_path, "c006-work")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 400)
    items, cursor = [], None
    while True:
        page = rumors.list_documents(tmp_path, cursor)
        assert len(references.encoded(page)) <= 400
        items.extend(page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert len(items) == 6
    assert items[-1]["identity"] is None and "missing" in items[-1]["diagnostic"]
    for cursor in ("bad", "-1", "999"):
        with pytest.raises(budget.InvalidCursorError):
            rumors.list_documents(tmp_path, cursor)


@pytest.mark.parametrize("collision", ["boss-directory", "rumors-directory", "document-directory", "symlink"])
def test_storage_collisions_do_not_modify_records(tmp_path, monkeypatch, collision):
    path = rumors._directory(tmp_path)
    if collision == "boss-directory":
        path.parent.write_text("Keep", encoding="utf-8")
    elif collision == "rumors-directory":
        path.parent.mkdir()
        path.write_text("Keep", encoding="utf-8")
    elif collision == "document-directory":
        (path / "c001-work.md").mkdir(parents=True)
    else:
        # Simulate a link on every platform, including Windows without symlink privileges.
        from pathlib import Path

        original = Path.is_symlink
        monkeypatch.setattr(Path, "is_symlink", lambda self: self == path or original(self))
    before = {p: p.read_bytes() for p in tmp_path.rglob("*.md") if p.is_file()}
    with pytest.raises(ValueError, match="collision"):
        rumors.write(tmp_path, "No", "c001")
    assert {p: p.read_bytes() for p in before} == before


def test_rumors_excluded_from_boss_discovery_dependencies_and_index(tmp_path):
    boss.create_boss(tmp_path, "b001-goal", "Goal", "Summary")
    boss.make_available(tmp_path, "b001-goal")
    before = boss_candidates.candidates(tmp_path)
    rumors.write(tmp_path, "uniquerumorcontent b999-new", "c001")
    assert boss.list_bosses(tmp_path, include_archived=True) == ["b001-goal"]
    assert references.Inventory(tmp_path).names("boss") == ["b001-goal"]
    assert boss_candidates.candidates(tmp_path) == before
    with pytest.raises(boss.BossNotFoundError):
        boss.assign_dependency(tmp_path, "b001-goal", "c001-work")
    assert search_index._classify(tmp_path, rumors._path(tmp_path, "c001-work")) is None
    search_index.rebuild_index(tmp_path)
    assert search_index.search(tmp_path, "uniquerumorcontent") == []
    assert search_index.search(tmp_path, "uniquerumorcontent", object_type="boss") == []
    assert json.loads(references.encoded(rumors.get(tmp_path, "c001")))["body"].startswith("uniquerumorcontent")
