from typing import Any

from cac.core import campaign as campaign_core
from cac.core import coupling, references
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp


@mcp.tool()
@references.inputs("campaign")
def campaign_reactivate(name: str, message: str) -> dict[str, Any]:
    """Reopen an unarchived completed campaign for review feedback with an attributed nonblank reason; preserve earlier closing history."""
    return campaign_to_dict(campaign_core.reactivate_campaign(resolve_project_root(), name, message))


def campaign_to_dict(campaign: campaign_core.Campaign) -> dict[str, Any]:
    return {
        "name": campaign.name,
        "status": campaign.status,
        "archived": campaign.archived,
        "body": campaign.body,
        "bosses": campaign.bosses,
    }


@mcp.tool()
@references.inputs("campaign")
def campaign_get(name: str) -> dict[str, Any]:
    """Show a campaign's frontmatter attributes and body - a long-running initiative, similar to a
    Jira Epic, expected to span many encounters. Body is truncated under the response budget; read
    the file directly at the reported path if truncated."""
    root = resolve_project_root()
    metadata, body = campaign_core.read_metadata(root, name)
    return {"metadata": metadata, "body": body, "boss_link": coupling.inspection(root, name)}


@mcp.tool()
@references.inputs("campaign")
def campaign_list(cursor: str | None = None) -> dict[str, Any]:
    """List campaign names with their current status, paged under the response budget."""
    entries = campaign_core.list_campaigns_with_status(resolve_project_root())
    return references.identity_page(
        resolve_project_root(), "campaign", [{"name": name, "status": status} for name, status in entries], cursor
    )


@mcp.tool()
@references.inputs("campaign", create=True)
def campaign_create(name: str, body: str, bosses: list[str] | None = None) -> dict[str, Any]:
    """Create a draft and atomically select optional eligible bosses (canonical names or refs)."""
    root = resolve_project_root()
    campaign_core.create_campaign(root, name, body, bosses)
    return campaign_to_dict(campaign_core.read_campaign(root, name))


@mcp.tool()
@references.inputs("campaign")
def campaign_set_bosses(name: str, bosses: list[str], message: str) -> dict[str, Any]:
    """Replace all draft boss membership atomically; an empty list clears it. Later states are locked."""
    root = resolve_project_root()
    campaign_core.set_bosses(root, name, bosses, message)
    return campaign_to_dict(campaign_core.read_campaign(root, name))


@mcp.tool()
@references.inputs("campaign")
def campaign_update(name: str, body: str) -> dict[str, Any]:
    """Replace an existing campaign's body. Fails once the campaign is 'completed' or 'abandoned' -
    its body is locked once its postmortem is recorded."""
    root = resolve_project_root()
    campaign_core.update_campaign(root, name, body)
    return campaign_to_dict(campaign_core.read_campaign(root, name))


@mcp.tool()
@references.inputs("campaign")
def campaign_delete(name: str) -> dict[str, str]:
    """Delete a bossless campaign only; origin history and reverse boss claims protect deletion."""
    path = campaign_core.delete_campaign(resolve_project_root(), name)
    return {"deleted": str(path)}


@mcp.tool()
@references.inputs("campaign")
def campaign_open(name: str) -> dict[str, Any]:
    """Move a campaign from 'draft' or 'paused' to 'open'. Only one campaign may be open at a
    time."""
    return campaign_to_dict(campaign_core.open_campaign(resolve_project_root(), name))


@mcp.tool()
@references.inputs("campaign")
def campaign_pause(name: str) -> dict[str, Any]:
    """Move a campaign from 'open' to 'paused'. Fails if the campaign has an open encounter."""
    return campaign_to_dict(campaign_core.pause_campaign(resolve_project_root(), name))


@mcp.tool()
@references.inputs("campaign")
def campaign_complete(name: str, message: str) -> dict[str, Any]:
    """Move a campaign from 'open' or 'paused' to 'completed'. Fails if the campaign has an open
    encounter. message is a required postmortem, recorded as a dated, attributed log entry; the
    campaign's body is locked while completed. All linked bosses are vanquished without design changes."""
    return campaign_to_dict(campaign_core.complete_campaign(resolve_project_root(), name, message))


@mcp.tool()
@references.inputs("campaign")
def campaign_abandon(name: str, message: str) -> dict[str, Any]:
    """Move a campaign from 'draft', 'open', or 'paused' to 'abandoned'. Fails if the campaign has
    an open encounter. message is a required postmortem, recorded as a dated, attributed log entry;
    the campaign's body is locked. Release all current boss links but retain the historical bosses list."""
    return campaign_to_dict(campaign_core.abandon_campaign(resolve_project_root(), name, message))


@mcp.tool()
@references.inputs("campaign")
def campaign_archive(name: str) -> dict[str, Any]:
    """Archive a campaign and all its encounters, moving them into .sourcebook/archive/ and setting
    archived: true on each. The campaign must already be 'completed' or 'abandoned', and every one
    of its encounters must also be 'completed' or 'abandoned' - status is preserved. Archive all current bosses too; abandoned history never controls released goals."""
    campaign, archived_encounters = campaign_core.archive_campaign(resolve_project_root(), name)
    return {**campaign_to_dict(campaign), "archived_encounters": archived_encounters}
