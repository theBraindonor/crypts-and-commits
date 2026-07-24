from datetime import datetime, timezone
from pathlib import Path

import pytest

from cac.core import campaign, encounter, frontmatter_utils, git_utils

_FIXED_TIME = datetime(2026, 7, 23, 18, 4, 12, tzinfo=timezone.utc)


def _set_identity(monkeypatch: pytest.MonkeyPatch, *, user: str = "John Hoff", when: datetime = _FIXED_TIME) -> None:
    monkeypatch.setattr(git_utils, "current_git_user", lambda root: user)
    monkeypatch.setattr(frontmatter_utils, "utcnow", lambda: when)


@pytest.fixture(autouse=True)
def _default_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_identity(monkeypatch)


def _open_encounter(tmp_path: Path, campaign_name: str, encounter_name: str) -> None:
    encounter.create_encounter(tmp_path, campaign_name, encounter_name, "Body.")
    encounter.review_encounter(tmp_path, campaign_name, encounter_name, "Looks good.")
    encounter.open_encounter(tmp_path, campaign_name, encounter_name)


def test_list_campaigns_returns_empty_when_no_directory(tmp_path: Path) -> None:
    assert campaign.list_campaigns(tmp_path) == []


def test_create_campaign_writes_frontmatter_and_body(tmp_path: Path) -> None:
    path = campaign.create_campaign(tmp_path, "opening-gambit", "# Opening Gambit\n\nThe party sets out.")

    assert path == tmp_path / ".sourcebook" / "campaigns" / "opening-gambit.md"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: opening-gambit" in text
    assert "status: draft" in text
    assert "The party sets out." in text


def test_create_campaign_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(campaign.InvalidCampaignNameError):
        campaign.create_campaign(tmp_path, "bad name!", "body")


def test_create_campaign_allows_periods(tmp_path: Path) -> None:
    path = campaign.create_campaign(tmp_path, "v0.1.0-bootstrapping", "body")

    assert path == tmp_path / ".sourcebook" / "campaigns" / "v0.1.0-bootstrapping.md"


@pytest.mark.parametrize("name", [".", ".."])
def test_create_campaign_rejects_reserved_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(campaign.InvalidCampaignNameError):
        campaign.create_campaign(tmp_path, name, "body")


def test_create_campaign_rejects_duplicate_name(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "duplicate", "first")

    with pytest.raises(campaign.CampaignAlreadyExistsError):
        campaign.create_campaign(tmp_path, "duplicate", "second")


def test_list_campaigns_returns_sorted_names(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "zeta", "z")
    campaign.create_campaign(tmp_path, "alpha", "a")

    assert campaign.list_campaigns(tmp_path) == ["alpha", "zeta"]


def test_template_body_returns_placeholder_text() -> None:
    assert "This campaign has not been described yet." in campaign.template_body()


def test_exists_reflects_created_campaign(tmp_path: Path) -> None:
    assert campaign.exists(tmp_path, "opening-gambit") is False

    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    assert campaign.exists(tmp_path, "opening-gambit") is True


def test_exists_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(campaign.InvalidCampaignNameError):
        campaign.exists(tmp_path, "bad name!")


def test_read_campaign_returns_name_status_and_body(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body text.")

    result = campaign.read_campaign(tmp_path, "opening-gambit")

    assert result.name == "opening-gambit"
    assert result.status == "draft"
    assert result.body.strip() == "Body text."


def test_read_campaign_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.read_campaign(tmp_path, "missing")


def test_read_metadata_returns_full_frontmatter_and_body(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body text.")
    campaign.open_campaign(tmp_path, "opening-gambit")

    metadata, body = campaign.read_metadata(tmp_path, "opening-gambit")

    assert metadata["name"] == "opening-gambit"
    assert metadata["status"] == "open"
    assert body.strip() == "Body text."


def test_read_metadata_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.read_metadata(tmp_path, "missing")


def test_update_campaign_replaces_body(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Original.")

    campaign.update_campaign(tmp_path, "opening-gambit", "Updated.")

    assert campaign.read_campaign(tmp_path, "opening-gambit").body.strip() == "Updated."


def test_update_campaign_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.update_campaign(tmp_path, "missing", "body")


def test_delete_campaign_removes_file(tmp_path: Path) -> None:
    path = campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    campaign.delete_campaign(tmp_path, "opening-gambit")

    assert not path.exists()


def test_delete_campaign_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.delete_campaign(tmp_path, "missing")


def test_create_campaign_sets_created_and_updated_fields(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    metadata, _ = campaign.read_metadata(tmp_path, "opening-gambit")

    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "John Hoff"
    assert metadata["updated_on"] == "2026-07-23T18:04:12Z"


def test_update_campaign_refreshes_updated_but_not_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Original.")

    later = datetime(2026, 8, 1, 9, 0, 0, tzinfo=timezone.utc)
    _set_identity(monkeypatch, user="Jane Doe", when=later)
    campaign.update_campaign(tmp_path, "opening-gambit", "Updated.")

    metadata, _ = campaign.read_metadata(tmp_path, "opening-gambit")
    assert metadata["created_by"] == "John Hoff"
    assert metadata["created_on"] == "2026-07-23T18:04:12Z"
    assert metadata["updated_by"] == "Jane Doe"
    assert metadata["updated_on"] == "2026-08-01T09:00:00Z"


def test_list_campaigns_with_status(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "zeta", "z")
    campaign.create_campaign(tmp_path, "alpha", "a")
    campaign.open_campaign(tmp_path, "alpha")

    assert campaign.list_campaigns_with_status(tmp_path) == [("alpha", "open"), ("zeta", "draft")]


def test_open_campaign_from_draft(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    result = campaign.open_campaign(tmp_path, "opening-gambit")

    assert result.status == "open"
    assert campaign.read_campaign(tmp_path, "opening-gambit").status == "open"


def test_open_campaign_missing_campaign_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.open_campaign(tmp_path, "missing")


def test_open_campaign_rejects_invalid_transition_from_completed(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    campaign.complete_campaign(tmp_path, "opening-gambit")

    with pytest.raises(campaign.InvalidCampaignTransitionError):
        campaign.open_campaign(tmp_path, "opening-gambit")


def test_open_campaign_conflicts_with_other_open_campaign(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "first", "Body.")
    campaign.create_campaign(tmp_path, "second", "Body.")
    campaign.open_campaign(tmp_path, "first")

    with pytest.raises(campaign.AnotherCampaignOpenError, match="first"):
        campaign.open_campaign(tmp_path, "second")

    assert campaign.read_campaign(tmp_path, "second").status == "draft"


def test_open_campaign_from_paused_succeeds(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    campaign.pause_campaign(tmp_path, "opening-gambit")

    result = campaign.open_campaign(tmp_path, "opening-gambit")

    assert result.status == "open"


def test_pause_campaign_from_open(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")

    result = campaign.pause_campaign(tmp_path, "opening-gambit")

    assert result.status == "paused"


def test_pause_campaign_rejects_invalid_transition_from_draft(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    with pytest.raises(campaign.InvalidCampaignTransitionError):
        campaign.pause_campaign(tmp_path, "opening-gambit")


def test_pause_campaign_blocked_by_open_encounter(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    _open_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    with pytest.raises(campaign.CampaignHasOpenEncountersError, match="goblin-ambush"):
        campaign.pause_campaign(tmp_path, "opening-gambit")

    assert campaign.read_campaign(tmp_path, "opening-gambit").status == "open"


def test_pause_campaign_allowed_once_encounter_completed(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    _open_encounter(tmp_path, "opening-gambit", "goblin-ambush")
    encounter.complete_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    result = campaign.pause_campaign(tmp_path, "opening-gambit")

    assert result.status == "paused"


def test_complete_campaign_from_open(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")

    result = campaign.complete_campaign(tmp_path, "opening-gambit")

    assert result.status == "completed"


def test_complete_campaign_from_paused(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    campaign.pause_campaign(tmp_path, "opening-gambit")

    result = campaign.complete_campaign(tmp_path, "opening-gambit")

    assert result.status == "completed"


def test_complete_campaign_blocked_by_open_encounter(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    _open_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    with pytest.raises(campaign.CampaignHasOpenEncountersError, match="goblin-ambush"):
        campaign.complete_campaign(tmp_path, "opening-gambit")


def test_complete_campaign_rejects_invalid_transition_from_draft(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    with pytest.raises(campaign.InvalidCampaignTransitionError):
        campaign.complete_campaign(tmp_path, "opening-gambit")


def test_abandon_campaign_from_draft(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    result = campaign.abandon_campaign(tmp_path, "opening-gambit")

    assert result.status == "abandoned"


def test_abandon_campaign_from_open(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")

    result = campaign.abandon_campaign(tmp_path, "opening-gambit")

    assert result.status == "abandoned"


def test_abandon_campaign_from_paused(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    campaign.pause_campaign(tmp_path, "opening-gambit")

    result = campaign.abandon_campaign(tmp_path, "opening-gambit")

    assert result.status == "abandoned"


def test_abandon_campaign_blocked_by_open_encounter(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    _open_encounter(tmp_path, "opening-gambit", "goblin-ambush")

    with pytest.raises(campaign.CampaignHasOpenEncountersError, match="goblin-ambush"):
        campaign.abandon_campaign(tmp_path, "opening-gambit")


def test_abandon_campaign_rejects_invalid_transition_from_completed(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")
    campaign.open_campaign(tmp_path, "opening-gambit")
    campaign.complete_campaign(tmp_path, "opening-gambit")

    with pytest.raises(campaign.InvalidCampaignTransitionError):
        campaign.abandon_campaign(tmp_path, "opening-gambit")


def test_pause_campaign_missing_campaign_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.pause_campaign(tmp_path, "missing")


def test_create_campaign_propagates_git_identity_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    assert not campaign.exists(tmp_path, "opening-gambit")


def test_update_campaign_propagates_git_identity_error_and_leaves_file_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Original.")
    path = campaign.campaign_dir(tmp_path) / "opening-gambit.md"
    before = path.read_text(encoding="utf-8")

    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        campaign.update_campaign(tmp_path, "opening-gambit", "Updated.")

    assert path.read_text(encoding="utf-8") == before


def test_open_campaign_propagates_git_identity_error_and_leaves_status_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    campaign.create_campaign(tmp_path, "opening-gambit", "Body.")

    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("no identity")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)

    with pytest.raises(git_utils.GitIdentityError):
        campaign.open_campaign(tmp_path, "opening-gambit")

    assert campaign.read_campaign(tmp_path, "opening-gambit").status == "draft"


def test_active_campaign_is_none_when_none_open(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "drafting", "Body.")

    assert campaign.active_campaign(tmp_path) is None


def test_active_campaign_returns_the_open_campaign(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "drafting", "Body.")
    campaign.create_campaign(tmp_path, "live", "Body.")
    campaign.open_campaign(tmp_path, "live")

    assert campaign.active_campaign(tmp_path) == "live"


def test_resolve_campaign_falls_back_to_active(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "live", "Body.")
    campaign.open_campaign(tmp_path, "live")

    assert campaign.resolve_campaign(tmp_path, None, require_mutable=True) == "live"


def test_resolve_campaign_without_active_raises(tmp_path: Path) -> None:
    campaign.create_campaign(tmp_path, "drafting", "Body.")

    with pytest.raises(campaign.NoActiveCampaignError):
        campaign.resolve_campaign(tmp_path, None, require_mutable=False)


def test_resolve_campaign_named_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(campaign.CampaignNotFoundError):
        campaign.resolve_campaign(tmp_path, "missing", require_mutable=False)


@pytest.mark.parametrize("require_mutable", [True, False])
def test_resolve_campaign_named_draft_is_allowed(tmp_path: Path, require_mutable: bool) -> None:
    campaign.create_campaign(tmp_path, "drafting", "Body.")

    assert campaign.resolve_campaign(tmp_path, "drafting", require_mutable=require_mutable) == "drafting"


@pytest.mark.parametrize("terminal", ["completed", "abandoned"])
def test_resolve_campaign_rejects_terminal_when_mutable_required(tmp_path: Path, terminal: str) -> None:
    campaign.create_campaign(tmp_path, "closed", "Body.")
    campaign.open_campaign(tmp_path, "closed")
    if terminal == "completed":
        campaign.complete_campaign(tmp_path, "closed")
    else:
        campaign.abandon_campaign(tmp_path, "closed")

    with pytest.raises(campaign.CampaignNotMutableError):
        campaign.resolve_campaign(tmp_path, "closed", require_mutable=True)


@pytest.mark.parametrize("terminal", ["completed", "abandoned"])
def test_resolve_campaign_allows_terminal_when_mutable_not_required(tmp_path: Path, terminal: str) -> None:
    campaign.create_campaign(tmp_path, "closed", "Body.")
    campaign.open_campaign(tmp_path, "closed")
    if terminal == "completed":
        campaign.complete_campaign(tmp_path, "closed")
    else:
        campaign.abandon_campaign(tmp_path, "closed")

    assert campaign.resolve_campaign(tmp_path, "closed", require_mutable=False) == "closed"
