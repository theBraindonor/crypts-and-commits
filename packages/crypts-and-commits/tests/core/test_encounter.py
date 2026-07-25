from datetime import datetime, timezone
from pathlib import Path

import pytest

from cac.core import campaign, encounter, frontmatter_utils, git_utils, region

_FIXED_TIME = datetime(2026, 7, 23, 18, 4, 12, tzinfo=timezone.utc)


def _set_identity(monkeypatch: pytest.MonkeyPatch, *, user: str = "John Hoff", when: datetime = _FIXED_TIME) -> None:
    monkeypatch.setattr(git_utils, "current_git_user", lambda root: user)
    monkeypatch.setattr(frontmatter_utils, "utcnow", lambda: when)


@pytest.fixture(autouse=True)
def _default_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_identity(monkeypatch)


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


def test_create_encounter_allows_periods(tmp_path: Path) -> None:
    _make_campaign(tmp_path, "v0.1.0-bootstrapping")

    path = encounter.create_encounter(tmp_path, "v0.1.0-bootstrapping", "fix-1.2", "body")

    assert path == tmp_path / ".sourcebook" / "encounters" / "v0.1.0-bootstrapping" / "fix-1.2.md"


@pytest.mark.parametrize("name", [".", ".."])
def test_create_encounter_rejects_reserved_names(tmp_path: Path, name: str) -> None:
    _make_campaign(tmp_path)

    with pytest.raises(encounter.InvalidEncounterNameError):
        encounter.create_encounter(tmp_path, "opening-gambit", name, "body")


def test_create_encounter_rejects_reserved_campaign_name(tmp_path: Path) -> None:
    with pytest.raises(campaign.InvalidCampaignNameError):
        encounter.create_encounter(tmp_path, "..", "goblin-ambush", "body")


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


def test_list_encounters_orders_by_updated_on_ascending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_campaign(tmp_path)
    _set_identity(monkeypatch, when=datetime(2026, 7, 3, tzinfo=timezone.utc))
    encounter.create_encounter(tmp_path, "opening-gambit", "middle", "m")
    _set_identity(monkeypatch, when=datetime(2026, 7, 1, tzinfo=timezone.utc))
    encounter.create_encounter(tmp_path, "opening-gambit", "oldest", "o")
    _set_identity(monkeypatch, when=datetime(2026, 7, 5, tzinfo=timezone.utc))
    encounter.create_encounter(tmp_path, "opening-gambit", "newest", "n")

    assert encounter.list_encounters(tmp_path, "opening-gambit") == ["oldest", "middle", "newest"]


def test_list_encounters_orders_by_updated_not_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_campaign(tmp_path)
    _set_identity(monkeypatch, when=datetime(2026, 7, 1, tzinfo=timezone.utc))
    encounter.create_encounter(tmp_path, "opening-gambit", "created-first", "a")
    _set_identity(monkeypatch, when=datetime(2026, 7, 2, tzinfo=timezone.utc))
    encounter.create_encounter(tmp_path, "opening-gambit", "created-second", "b")

    # Touch the first-created encounter so its updated_on is the most recent.
    _set_identity(monkeypatch, when=datetime(2026, 7, 3, tzinfo=timezone.utc))
    encounter.update_encounter(tmp_path, "opening-gambit", "created-first", "a2")

    assert encounter.list_encounters(tmp_path, "opening-gambit") == ["created-second", "created-first"]


def test_list_encounters_sorts_missing_updated_on_first(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "has-timestamp", "t")
    directory = encounter.encounter_dir(tmp_path, "opening-gambit")
    (directory / "no-timestamp.md").write_text(
        "---\nname: no-timestamp\nstatus: draft\n---\n\nBody.\n", encoding="utf-8"
    )

    assert encounter.list_encounters(tmp_path, "opening-gambit") == ["no-timestamp", "has-timestamp"]


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
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
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


@pytest.mark.parametrize(
    "advance",
    [
        lambda tmp_path: encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore."),
        lambda tmp_path: (
            encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore."),
            encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush"),
        ),
        lambda tmp_path: (
            encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore."),
            encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush"),
            encounter.complete_encounter(tmp_path, "opening-gambit", "goblin-ambush"),
        ),
        lambda tmp_path: encounter.abandon_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Not needed."),
    ],
    ids=["reviewed", "open", "completed", "abandoned"],
)
def test_update_encounter_rejects_once_not_draft(tmp_path: Path, advance) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Original.")
    advance(tmp_path)

    with pytest.raises(encounter.EncounterNotDraftError):
        encounter.update_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Updated.")

    assert encounter.read_encounter(tmp_path, "opening-gambit", "goblin-ambush").body.strip().startswith("Original.")


def test_delete_encounter_removes_file(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    path = encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    encounter.delete_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    assert not path.exists()


def test_delete_encounter_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.delete_encounter(tmp_path, "opening-gambit", "missing")


def test_encounter_path_returns_on_disk_path(tmp_path: Path) -> None:
    expected = tmp_path / ".sourcebook" / "encounters" / "opening-gambit" / "goblin-ambush.md"
    assert encounter.encounter_path(tmp_path, "opening-gambit", "goblin-ambush") == expected


def test_review_encounter_transitions_status_and_appends_message(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Looks good.")

    assert result.status == "reviewed"
    body = encounter.read_encounter(tmp_path, "opening-gambit", "goblin-ambush").body
    assert "## Log" in body
    assert "### Review" in body
    assert "Looks good." in body


@pytest.mark.parametrize("message", ["", "   "])
def test_review_encounter_requires_message(tmp_path: Path, message: str) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    with pytest.raises(encounter.EncounterMessageRequiredError):
        encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", message)


def test_review_encounter_rejects_when_not_draft(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "First review.")

    with pytest.raises(encounter.InvalidEncounterTransitionError):
        encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Second review.")


def test_review_encounter_missing_encounter_raises(tmp_path: Path) -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.review_encounter(tmp_path, "opening-gambit", "missing", "Looks good.")


@pytest.mark.parametrize(
    "advance",
    [
        lambda tmp_path: None,
        lambda tmp_path: encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore."),
        lambda tmp_path: (
            encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore."),
            encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush"),
        ),
    ],
    ids=["draft", "reviewed", "open"],
)
def test_abandon_encounter_succeeds_from_non_terminal_statuses(tmp_path: Path, advance) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    advance(tmp_path)

    result = encounter.abandon_encounter(tmp_path, "opening-gambit", "goblin-ambush", "No longer needed.")

    assert result.status == "abandoned"
    body = encounter.read_encounter(tmp_path, "opening-gambit", "goblin-ambush").body
    assert "### Abandoned" in body
    assert "No longer needed." in body


def test_abandon_encounter_rejects_from_completed(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore.")
    encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush")
    encounter.complete_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    with pytest.raises(encounter.InvalidEncounterTransitionError):
        encounter.abandon_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Too late.")


def test_abandon_encounter_rejects_from_abandoned(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.abandon_encounter(tmp_path, "opening-gambit", "goblin-ambush", "First.")

    with pytest.raises(encounter.InvalidEncounterTransitionError):
        encounter.abandon_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Second.")


@pytest.mark.parametrize("message", ["", "   "])
def test_abandon_encounter_requires_message(tmp_path: Path, message: str) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    with pytest.raises(encounter.EncounterMessageRequiredError):
        encounter.abandon_encounter(tmp_path, "opening-gambit", "goblin-ambush", message)


def test_open_encounter_transitions_from_reviewed_without_message(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore.")

    result = encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    assert result.status == "open"
    assert "### Opened" not in result.body


def test_open_encounter_transitions_from_reviewed_with_message(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore.")

    result = encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Go ahead.")

    assert result.status == "open"
    assert "### Opened" in result.body
    assert "Go ahead." in result.body


def test_open_encounter_rejects_from_draft(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    with pytest.raises(encounter.InvalidEncounterTransitionError):
        encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush")


def test_complete_encounter_transitions_from_open(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore.")
    encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    result = encounter.complete_encounter(tmp_path, "opening-gambit", "goblin-ambush", "All verified.")

    assert result.status == "completed"
    assert "### Completed" in result.body
    assert "All verified." in result.body


def test_complete_encounter_rejects_from_reviewed(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore.")

    with pytest.raises(encounter.InvalidEncounterTransitionError):
        encounter.complete_encounter(tmp_path, "opening-gambit", "goblin-ambush")


@pytest.mark.parametrize("status", ["reviewed", "open"])
def test_record_message_allowed_in_reviewed_and_open_statuses(tmp_path: Path, status: str) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore.")
    if status == "open":
        encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    result = encounter.record_message(tmp_path, "opening-gambit", "goblin-ambush", "Noted a deviation.")

    assert result.status == status
    assert "### Message" in result.body
    assert "Noted a deviation." in result.body


@pytest.mark.parametrize(
    "advance",
    [
        lambda tmp_path: None,
        lambda tmp_path: (
            encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore."),
            encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush"),
            encounter.complete_encounter(tmp_path, "opening-gambit", "goblin-ambush"),
        ),
        lambda tmp_path: encounter.abandon_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Nope."),
    ],
    ids=["draft", "completed", "abandoned"],
)
def test_record_message_rejects_outside_reviewed_or_open(tmp_path: Path, advance) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    advance(tmp_path)

    with pytest.raises(encounter.InvalidEncounterTransitionError):
        encounter.record_message(tmp_path, "opening-gambit", "goblin-ambush", "Noted.")


@pytest.mark.parametrize("message", ["", "   "])
def test_record_message_requires_message(tmp_path: Path, message: str) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore.")

    with pytest.raises(encounter.EncounterMessageRequiredError):
        encounter.record_message(tmp_path, "opening-gambit", "goblin-ambush", message)


def test_record_message_missing_encounter_raises(tmp_path: Path) -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.record_message(tmp_path, "opening-gambit", "missing", "Noted.")


def test_record_message_multiple_calls_append_multiple_entries_under_one_log_section(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Checked lore.")
    encounter.open_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    encounter.record_message(tmp_path, "opening-gambit", "goblin-ambush", "First note.")
    result = encounter.record_message(tmp_path, "opening-gambit", "goblin-ambush", "Second note.")

    assert result.body.count("## Log") == 1
    assert result.body.count("### Message") == 2
    assert result.body.index("First note.") < result.body.index("Second note.")


def test_assign_region_sets_region_on_encounter_only(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    assert result.regions == ["northlands"]
    region_text = (tmp_path / ".sourcebook" / "region" / "northlands.md").read_text(encoding="utf-8")
    assert "goblin-ambush" not in region_text


def test_assign_region_is_idempotent(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")
    result = encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    assert result.regions == ["northlands"]


def test_encounter_can_be_assigned_to_multiple_regions(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    region.create_region(tmp_path, "southlands", "Body.", "Summary.")
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
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")

    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.assign_region(tmp_path, "opening-gambit", "missing", "northlands")


def test_unassign_region_clears_region(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    result = encounter.unassign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    assert result.regions == []


def test_unassign_region_leaves_other_regions(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    region.create_region(tmp_path, "southlands", "Body.", "Summary.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "southlands")

    result = encounter.unassign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    assert result.regions == ["southlands"]


def test_unassign_region_missing_encounter_raises(tmp_path: Path) -> None:
    with pytest.raises(encounter.EncounterNotFoundError):
        encounter.unassign_region(tmp_path, "opening-gambit", "missing", "northlands")


def test_create_encounter_sets_created_and_updated_fields(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    metadata, _ = encounter.read_metadata(tmp_path, "opening-gambit", "goblin-ambush")

    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "John Hoff"
    assert metadata["updated_on"] == "2026-07-23T18:04:12Z"


def test_touching_an_encounter_refreshes_updated_but_not_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    later = datetime(2026, 8, 1, 9, 0, 0, tzinfo=timezone.utc)
    _set_identity(monkeypatch, user="Jane Doe", when=later)
    encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Looks good.")

    metadata, _ = encounter.read_metadata(tmp_path, "opening-gambit", "goblin-ambush")
    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "Jane Doe"
    assert metadata["updated_on"] == "2026-08-01T09:00:00Z"


def test_assign_region_refreshes_updated_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_campaign(tmp_path)
    region.create_region(tmp_path, "northlands", "Body.", "Summary.")
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    later = datetime(2026, 8, 1, 9, 0, 0, tzinfo=timezone.utc)
    _set_identity(monkeypatch, user="Jane Doe", when=later)
    encounter.assign_region(tmp_path, "opening-gambit", "goblin-ambush", "northlands")

    metadata, _ = encounter.read_metadata(tmp_path, "opening-gambit", "goblin-ambush")
    assert metadata["updated_by"] == "Jane Doe"
    assert metadata["updated_on"] == "2026-08-01T09:00:00Z"


def test_log_entry_includes_timestamp_and_user(tmp_path: Path) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    result = encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Looks good.")

    assert "### Review - 2026-07-23T18:04:12Z - John Hoff" in result.body


def test_create_encounter_propagates_git_identity_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _make_campaign(tmp_path)

    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")

    assert not encounter.exists(tmp_path, "opening-gambit", "goblin-ambush")


def test_update_encounter_propagates_git_identity_error_and_leaves_file_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Original.")
    path = encounter.encounter_dir(tmp_path, "opening-gambit") / "goblin-ambush.md"
    before = path.read_text(encoding="utf-8")

    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        encounter.update_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Updated.")

    assert path.read_text(encoding="utf-8") == before


def test_review_encounter_propagates_git_identity_error_and_leaves_file_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_campaign(tmp_path)
    encounter.create_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Body.")
    path = encounter.encounter_dir(tmp_path, "opening-gambit") / "goblin-ambush.md"
    before = path.read_text(encoding="utf-8")

    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        encounter.review_encounter(tmp_path, "opening-gambit", "goblin-ambush", "Looks good.")

    assert path.read_text(encoding="utf-8") == before
    assert encounter.read_encounter(tmp_path, "opening-gambit", "goblin-ambush").status == "draft"
