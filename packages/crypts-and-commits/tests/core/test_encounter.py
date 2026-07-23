from pathlib import Path

import pytest

from cac.core import campaign, encounter, region


def _make_campaign(tmp_path: Path, name: str = "opening-gambit") -> None:
    campaign.create_campaign(tmp_path, name, "Body.")


def test_list_encounters_returns_empty_when_no_directory(tmp_path: Path) -> None:
    assert encounter.list_encounters(tmp_path, "opening-gambit") == []


def test_create_encounter_requires_existing_campaign(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        encounter.create_encounter(tmp_path, "missing", "goblin-ambush", "body")


def test_create_encounter_writes_frontmatter_and_body(tmp_path: Path) -> None:
    _make_campaign(tmp_path)

    path = encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "## Requirements\n\nStop them.")

    assert path == tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: goblin-ambush" in text
    assert "campaign: opening-gambit" in text
    assert "status: draft" in text
    assert "Stop them." in text


def test_create_encounter_rejects_invalid_name(tmp_path: Path) -> None:
    _make_campaign(tmp_path)

    with pytest.raises(encounter.InvalidEncounterNameError):
        encounter.create_encounter(tmp_path, "opening-gambit", "bad name!", "body")


def test_create_encounter_rejects_duplicate_name(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "duplicate", "first")

    with pytest.raises(encounter.EncounterAlreadyExistsError):
        encounter.create_encounter(tmp_path, "opening-gambit", "duplicate", "second")


def test_encounters_are_scoped_per_campaign(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "campaign-one")
    _make_campaign(tmp_path, "campaign-two")

    encounter.create_encounter(tmp_path, "campaign-one", "shared-name", "first")
    encounter.create_encounter(tmp_path, "campaign-two", "shared-name", "second")

    assert encounter.list_encounters(tmp_path, "campaign-one") == ["shared-name"]
    assert encounter.list_encounters(tmp_path, "campaign-two") == ["shared-name"]
    assert encounter.read_encounter(tmp_path, "campaign-one", "shared-name").body.strip() == "first"
    assert encounter.read_encounter(tmp_path, "campaign-two", "shared-name").body.strip() == "second"


def test_list_encounters_returns_sorted_names(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "zeta", "z")
    encounter.create_encounter(tmp_path, "opening-gambit", "alpha", "a")

    assert encounter.list_encounters(tmp_path, "opening-gambit") == ["alpha", "zeta"]


def test_template_body_contains_all_sections() -> None:
    body = encounter.template_body()

    assert "## Requirements" in body
    assert "## Rationale" in body
    assert "## Plan" in body
    assert "## Verification" in body


def test_exists_reflects_created_encounter(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    assert encounter.exists(tmp_path, "opening-gambit", "goblin-ambush") is False

    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    assert encounter.exists(tmp_path, "opening-gambit", "goblin-ambush") is True


def test_exists_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(encounter.InvalidEncounterNameError):
        encounter.exists(tmp_path, "opening-gambit", "bad name!")


def test_read_encounter_returns_metadata_and_body(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body text.")

    result = encounter.read_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    assert result.name == "goblin-ambush"
    assert result.campaign == "opening-gambit"
    assert result.status == "draft"
    assert result.regions == []
    assert result.body.strip() == "Body text."


def test_read_encounter_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.read_encounter(tmp_path, "opening-gambit", "missing")


def test_read_metadata_returns_full_frontmatter_and_body(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body text.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    metadata, body = encounter.read_metadata(tmp_path, "opening-gambit", "goblin-ambush")

    assert metadata["name"] == "goblin-ambush"
    assert metadata["campaign"] == "opening-gambit"
    assert metadata["status"] == "draft"
    assert metadata["regions"] == ["northlands"]
    assert body.strip() == "Body text."


def test_read_metadata_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.read_metadata(tmp_path, "opening-gambit", "missing")


def test_update_encounter_replaces_body(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Original.")

    encounter.update_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Updated.")

    assert encounter.read_encounter(tmp_path, "opening-gambit", "goblin-ambush").body.strip() == "Updated."


def test_update_encounter_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.update_encounter(tmp_path, "opening-gambit", "missing", "body")


def test_delete_encounter_removes_file(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    path = encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    encounter.delete_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    assert not path.exists()


def test_delete_encounter_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.delete_encounter(tmp_path, "opening-gambit", "missing")


def test_set_status_updates_status(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = encounter.set_status(tmp_path, "opening-gambit", "goblin-ambush", "abandoned")

    assert result.status == "abandoned"
    assert encounter.read_encounter(tmp_path, "opening-gambit", "goblin-ambush").status == "abandoned"


def test_set_status_rejects_invalid_status(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    with pytest.raises(encounter.InvalidEncounterStatusError):
        encounter.set_status(tmp_path, "opening-gambit", "goblin-ambush", "cancelled")


def test_set_status_missing_encounter_raises(tmp_path: Path) -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.set_status(tmp_path, "opening-gambit", "missing", "open")


def test_assign_region_sets_region_on_encounter_only(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    assert result.regions == ["northlands"]
    region_text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "goblin-ambush" not in region_text


def test_assign_region_is_idempotent(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")
    result = encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    assert result.regions == ["northlands"]


def test_encounter_can_be_assigned_to_multiple_regions(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.")
    region.create_region(tmp_path, "southlands", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")
    result = encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "southlands")

    assert result.regions == ["northlands", "southlands"]


def test_assign_region_missing_region_raises(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    with pytest.raises(region.RegionNotFoundError):
        encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "missing")


def test_assign_region_missing_encounter_raises(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.")

    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.assign_region(tmp_path, "opening-gambit", "missing", "northlands")


def test_unassign_region_clears_region(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    result = encounter.unassign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    assert result.regions == []


def test_unassign_region_leaves_other_regions(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.")
    region.create_region(tmp_path, "southlands", "Body.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "southlands")

    result = encounter.unassign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    assert result.regions == ["southlands"]


def test_unassign_region_missing_encounter_raises(tmp_path: Path) -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.unassign_region(tmp_path, "opening-gambit", "missing", "northlands")
