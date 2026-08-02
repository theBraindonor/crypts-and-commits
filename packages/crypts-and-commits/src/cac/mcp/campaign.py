from pathlib import Path
from typing import Any

from cac.core import budget as budget_core
from cac.core import campaign as campaign_core
from cac.mcp.instance import mcp


def campaign_to_dict(campaign: campaign_core.Campaign) -> dict[str, Any]:
    return {
        "name": campaign.name,
        "status": campaign.status,
        "archived": campaign.archived,
        "body": campaign.body,
    }


@mcp.tool()
def campaign_get(name: str) -> dict[str, Any]:
    """Show a campaign's frontmatter attributes and body - a long-running initiative, similar to a
    Jira Epic, expected to span many encounters. Body is truncated under the response budget; read
    the file directly at the reported path if truncated."""
    root = Path.cwd()
    metadata, body = campaign_core.read_metadata(root, name)
    body = budget_core.truncate_body(body, campaign_core.campaign_path(root, name))
    return {"metadata": metadata, "body": body}


@mcp.tool()
def campaign_list(cursor: str | None = None) -> dict[str, Any]:
    """List campaign names with their current status, paged under the response budget."""
    entries = campaign_core.list_campaigns_with_status(Path.cwd())
    page = budget_core.paginate(entries, cursor, render=lambda entry: f"{entry[0]} ({entry[1]})")
    return {
        "items": [{"name": name, "status": status} for name, status in page.items],
        "next_cursor": page.next_cursor,
    }


@mcp.tool()
def campaign_create(name: str, body: str) -> dict[str, Any]:
    """Create a new campaign, starting in 'draft' status."""
    root = Path.cwd()
    campaign_core.create_campaign(root, name, body)
    return campaign_to_dict(campaign_core.read_campaign(root, name))


@mcp.tool()
def campaign_update(name: str, body: str) -> dict[str, Any]:
    """Replace an existing campaign's body. Fails once the campaign is 'completed' or 'abandoned' -
    its body is locked once its postmortem is recorded."""
    root = Path.cwd()
    campaign_core.update_campaign(root, name, body)
    return campaign_to_dict(campaign_core.read_campaign(root, name))


@mcp.tool()
def campaign_delete(name: str) -> dict[str, str]:
    """Delete a campaign file."""
    path = campaign_core.delete_campaign(Path.cwd(), name)
    return {"deleted": str(path)}


@mcp.tool()
def campaign_open(name: str) -> dict[str, Any]:
    """Move a campaign from 'draft' or 'paused' to 'open'. Only one campaign may be open at a
    time."""
    return campaign_to_dict(campaign_core.open_campaign(Path.cwd(), name))


@mcp.tool()
def campaign_pause(name: str) -> dict[str, Any]:
    """Move a campaign from 'open' to 'paused'. Fails if the campaign has an open encounter."""
    return campaign_to_dict(campaign_core.pause_campaign(Path.cwd(), name))


@mcp.tool()
def campaign_complete(name: str, message: str) -> dict[str, Any]:
    """Move a campaign from 'open' or 'paused' to 'completed'. Fails if the campaign has an open
    encounter. message is a required postmortem, recorded as a dated, attributed log entry; the
    campaign's body is locked thereafter."""
    return campaign_to_dict(campaign_core.complete_campaign(Path.cwd(), name, message))


@mcp.tool()
def campaign_abandon(name: str, message: str) -> dict[str, Any]:
    """Move a campaign from 'draft', 'open', or 'paused' to 'abandoned'. Fails if the campaign has
    an open encounter. message is a required postmortem, recorded as a dated, attributed log entry;
    the campaign's body is locked thereafter."""
    return campaign_to_dict(campaign_core.abandon_campaign(Path.cwd(), name, message))


@mcp.tool()
def campaign_archive(name: str) -> dict[str, Any]:
    """Archive a campaign and all its encounters, moving them into .sourcebook/archive/ and setting
    archived: true on each. The campaign must already be 'completed' or 'abandoned', and every one
    of its encounters must also be 'completed' or 'abandoned' - status is preserved, not replaced."""
    campaign, archived_encounters = campaign_core.archive_campaign(Path.cwd(), name)
    return {**campaign_to_dict(campaign), "archived_encounters": archived_encounters}
