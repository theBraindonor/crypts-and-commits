from pathlib import Path

import pytest
from cac.core import campaign, encounter, git_utils, region
from cac.mcp import encounter as mcp_encounter


@pytest.fixture(autouse=True)
def _use_tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def _default_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(git_utils, "current_git_user", lambda root: "John Hoff")


@pytest.fixture(autouse=True)
def _active_campaign(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")


def test_encounter_get_defaults_to_active_campaign(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Encounter body.")

    result = mcp_encounter.encounter_get("goblin-ambush")

    assert result["body"].strip() == "Encounter body."
    assert result["metadata"]["status"] == "draft"


def test_encounter_get_missing_raises() -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        mcp_encounter.encounter_get("missing")


def test_encounter_get_no_active_campaign_raises(tmp_path: Path) -> None:
    campaign.pause_campaign(tmp_path, "opening-gambit")

    with pytest.raises(campaign.NoActiveCampaignError):
        mcp_encounter.encounter_get("goblin-ambush")


def test_encounter_list_returns_items_and_cursor(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = mcp_encounter.encounter_list()

    assert result["items"] == ["goblin-ambush"]
    assert result["next_cursor"] is None


def test_encounter_order_returns_dependency_order(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "first", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "second", "Body.")
    encounter.assign_dependency(tmp_path, "opening-gambit", "second", "first")

    result = mcp_encounter.encounter_order()

    assert result == [
        {"name": "first", "status": "draft", "depends_on": []},
        {"name": "second", "status": "draft", "depends_on": ["first"]},
    ]


def test_encounter_create_returns_new_encounter() -> None:
    result = mcp_encounter.encounter_create("goblin-ambush", "Encounter body.")

    assert result["name"] == "goblin-ambush"
    assert result["campaign"] == "opening-gambit"
    assert result["status"] == "draft"
    assert result["body"].strip() == "Encounter body."


def test_encounter_update_replaces_body(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Old.")

    result = mcp_encounter.encounter_update("goblin-ambush", "New.")

    assert result["body"].strip() == "New."


def test_encounter_delete_removes_file(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = mcp_encounter.encounter_delete("goblin-ambush")

    assert not encounter.exists(tmp_path, "opening-gambit", "goblin-ambush")
    assert result["deleted"].endswith("goblin-ambush.md")


def test_encounter_review_requires_region(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    with pytest.raises(encounter.EncounterRegionRequiredError):
        mcp_encounter.encounter_review("goblin-ambush", "Looks solid.")


def test_encounter_review_locks_and_transitions(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    region.create_region(tmp_path, "backend", "Body.", "Summary.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "backend")

    result = mcp_encounter.encounter_review("goblin-ambush", "Looks solid.")

    assert result["status"] == "reviewed"


def test_encounter_review_requires_message(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    region.create_region(tmp_path, "backend", "Body.", "Summary.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "backend")

    with pytest.raises(encounter.EncounterMessageRequiredError):
        mcp_encounter.encounter_review("goblin-ambush", "")


def test_encounter_open_and_complete(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    region.create_region(tmp_path, "backend", "Body.", "Summary.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "backend")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Looks solid.")

    opened = mcp_encounter.encounter_open("goblin-ambush")
    assert opened["status"] == "open"

    completed = mcp_encounter.encounter_complete("goblin-ambush", message="Done.")
    assert completed["status"] == "completed"


def test_encounter_record_message_appends_without_status_change(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    region.create_region(tmp_path, "backend", "Body.", "Summary.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "backend")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Looks solid.")

    result = mcp_encounter.encounter_record_message("goblin-ambush", "Heads up.")

    assert result["status"] == "reviewed"
    assert "Heads up." in result["body"]


def test_encounter_abandon_requires_message(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = mcp_encounter.encounter_abandon("goblin-ambush", "Scope cut.")

    assert result["status"] == "abandoned"


def test_encounter_assign_region_and_unassign_region(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    region.create_region(tmp_path, "backend", "Body.", "Summary.")

    assigned = mcp_encounter.encounter_assign_region("goblin-ambush", "backend")
    assert assigned["regions"] == ["backend"]

    unassigned = mcp_encounter.encounter_unassign_region("goblin-ambush", "backend")
    assert unassigned["regions"] == []


def test_encounter_assign_region_rejected_once_open(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    region.create_region(tmp_path, "backend", "Body.", "Summary.")
    region.create_region(tmp_path, "frontend", "Body.", "Summary.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "backend")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Looks solid.")
    encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    with pytest.raises(encounter.EncounterRegionMutationError):
        mcp_encounter.encounter_assign_region("goblin-ambush", "frontend")


def test_encounter_assign_dependency_and_unassign_dependency(tmp_path: Path) -> None:
    encounter.create_encounter(tmp_path, "opening-gambit", "first", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "second", "Body.")

    assigned = mcp_encounter.encounter_assign_dependency("second", "first")
    assert assigned["depends_on"] == ["first"]

    unassigned = mcp_encounter.encounter_unassign_dependency("second", "first")
    assert unassigned["depends_on"] == []
