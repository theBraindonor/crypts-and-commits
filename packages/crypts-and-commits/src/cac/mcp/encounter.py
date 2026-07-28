from pathlib import Path
from typing import Any

from cac.core import budget as budget_core
from cac.core import campaign as campaign_core
from cac.core import encounter as encounter_core
from cac.mcp.instance import mcp


def encounter_to_dict(encounter: encounter_core.Encounter) -> dict[str, Any]:
    return {
        "name": encounter.name,
        "campaign": encounter.campaign,
        "status": encounter.status,
        "regions": encounter.regions,
        "depends_on": encounter.depends_on,
        "body": encounter.body,
    }


def _resolve_campaign(campaign: str | None, *, require_mutable: bool) -> str:
    return campaign_core.resolve_campaign(Path.cwd(), campaign, require_mutable=require_mutable)


@mcp.tool()
def encounter_get(name: str, campaign: str | None = None) -> dict[str, Any]:
    """Show an encounter's frontmatter attributes and body - a concrete unit of work within a
    campaign, with Requirements/Rationale/Plan/Verification sections. Body is truncated under the
    response budget; read the file directly at the reported path if truncated. campaign defaults to
    the active (open) campaign when omitted."""
    root = Path.cwd()
    resolved = _resolve_campaign(campaign, require_mutable=False)
    metadata, body = encounter_core.read_metadata(root, resolved, name)
    body = budget_core.truncate_body(body, encounter_core.encounter_path(root, resolved, name))
    return {"metadata": metadata, "body": body}


@mcp.tool()
def encounter_list(campaign: str | None = None, cursor: str | None = None) -> dict[str, Any]:
    """List encounter names in a campaign, oldest-updated first, paged under the response budget.
    campaign defaults to the active (open) campaign when omitted."""
    resolved = _resolve_campaign(campaign, require_mutable=False)
    names = encounter_core.list_encounters(Path.cwd(), resolved)
    page = budget_core.paginate(names, cursor)
    return {"items": page.items, "next_cursor": page.next_cursor}


@mcp.tool()
def encounter_order(campaign: str | None = None) -> list[dict[str, Any]]:
    """Show every campaign encounter in deterministic dependency order, with status and direct
    dependencies. campaign defaults to the active (open) campaign when omitted."""
    resolved = _resolve_campaign(campaign, require_mutable=False)
    ordered = encounter_core.order_encounters(Path.cwd(), resolved)
    return [{"name": item.name, "status": item.status, "depends_on": item.depends_on} for item in ordered]


@mcp.tool()
def encounter_create(name: str, body: str, campaign: str | None = None) -> dict[str, Any]:
    """Create a new encounter, starting in 'draft' status. campaign defaults to the active (open)
    campaign when omitted; it must already exist and not be completed/abandoned."""
    root = Path.cwd()
    resolved = _resolve_campaign(campaign, require_mutable=True)
    encounter_core.create_encounter(root, resolved, name, body)
    return encounter_to_dict(encounter_core.read_encounter(root, resolved, name))


@mcp.tool()
def encounter_update(name: str, body: str, campaign: str | None = None) -> dict[str, Any]:
    """Replace an existing encounter's body. Only permitted while status is 'draft'."""
    root = Path.cwd()
    resolved = _resolve_campaign(campaign, require_mutable=True)
    encounter_core.update_encounter(root, resolved, name, body)
    return encounter_to_dict(encounter_core.read_encounter(root, resolved, name))


@mcp.tool()
def encounter_delete(name: str, campaign: str | None = None) -> dict[str, str]:
    """Delete an encounter file. Fails while another encounter depends on it."""
    resolved = _resolve_campaign(campaign, require_mutable=True)
    path = encounter_core.delete_encounter(Path.cwd(), resolved, name)
    return {"deleted": str(path)}


@mcp.tool()
def encounter_review(name: str, message: str, campaign: str | None = None) -> dict[str, Any]:
    """Move an encounter from 'draft' to 'reviewed' after a lore review. Requires at least one
    assigned region. message is required and permanently locks its
    Requirements/Rationale/Plan/Verification sections against further replacement."""
    resolved = _resolve_campaign(campaign, require_mutable=True)
    return encounter_to_dict(encounter_core.review_encounter(Path.cwd(), resolved, name, message))


@mcp.tool()
def encounter_open(name: str, campaign: str | None = None, message: str | None = None) -> dict[str, Any]:
    """Move an encounter from 'reviewed' to 'open' and begin execution. Fails until every direct
    dependency is 'completed'. message is optional."""
    resolved = _resolve_campaign(campaign, require_mutable=True)
    return encounter_to_dict(encounter_core.open_encounter(Path.cwd(), resolved, name, message))


@mcp.tool()
def encounter_record_message(name: str, message: str, campaign: str | None = None) -> dict[str, Any]:
    """Append a message to an encounter without changing its status. Valid while status is
    'reviewed' or 'open'."""
    resolved = _resolve_campaign(campaign, require_mutable=True)
    return encounter_to_dict(encounter_core.record_message(Path.cwd(), resolved, name, message))


@mcp.tool()
def encounter_complete(name: str, campaign: str | None = None, message: str | None = None) -> dict[str, Any]:
    """Move an encounter from 'open' to 'completed' once verification passes. message is optional."""
    resolved = _resolve_campaign(campaign, require_mutable=True)
    return encounter_to_dict(encounter_core.complete_encounter(Path.cwd(), resolved, name, message))


@mcp.tool()
def encounter_abandon(name: str, message: str, campaign: str | None = None) -> dict[str, Any]:
    """Move an encounter from 'draft', 'reviewed', or 'open' to 'abandoned'. message is required.
    Not reachable once 'completed'."""
    resolved = _resolve_campaign(campaign, require_mutable=True)
    return encounter_to_dict(encounter_core.abandon_encounter(Path.cwd(), resolved, name, message))


@mcp.tool()
def encounter_assign_region(name: str, region: str, campaign: str | None = None) -> dict[str, Any]:
    """Assign an encounter to a region. An encounter may be assigned to one or more regions; the
    link is recorded only on the encounter."""
    resolved = _resolve_campaign(campaign, require_mutable=True)
    return encounter_to_dict(encounter_core.assign_region(Path.cwd(), resolved, name, region))


@mcp.tool()
def encounter_unassign_region(name: str, region: str, campaign: str | None = None) -> dict[str, Any]:
    """Unassign an encounter from a region."""
    resolved = _resolve_campaign(campaign, require_mutable=True)
    return encounter_to_dict(encounter_core.unassign_region(Path.cwd(), resolved, name, region))


@mcp.tool()
def encounter_assign_dependency(name: str, dependency: str, campaign: str | None = None) -> dict[str, Any]:
    """Add a direct prerequisite to an encounter while it is 'draft'."""
    resolved = _resolve_campaign(campaign, require_mutable=True)
    return encounter_to_dict(encounter_core.assign_dependency(Path.cwd(), resolved, name, dependency))


@mcp.tool()
def encounter_unassign_dependency(name: str, dependency: str, campaign: str | None = None) -> dict[str, Any]:
    """Remove a direct prerequisite while the dependent encounter is 'draft'."""
    resolved = _resolve_campaign(campaign, require_mutable=True)
    return encounter_to_dict(encounter_core.unassign_dependency(Path.cwd(), resolved, name, dependency))
