from typing import Any

from cac.core import campaign as campaign_core
from cac.core import prime as prime_core
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp
from cac.mcp.world import world_to_dict


def _prime_bundle_to_dict(bundle: prime_core.PrimeBundle) -> dict[str, Any]:
    return {
        "world": world_to_dict(bundle.world),
        "world_lore": [{"name": entry.name, "summary": entry.summary} for entry in bundle.world_lore],
        "regions": [
            {
                "name": region.name,
                "summary": region.summary,
                "path": region.path,
                "assigned_lore": region.assigned_lore,
            }
            for region in bundle.regions
        ],
        "active_campaign": bundle.active_campaign,
        "campaign_body": bundle.campaign_body,
    }


@mcp.tool()
def prime_get() -> dict[str, Any]:
    """Assemble the global prime bundle: world (full) + world-assigned enabled lore
    (summaries) + region map (summary + path + assigned-lore edge names per region) +
    the active campaign (full body, not its encounter list)."""
    return _prime_bundle_to_dict(prime_core.assemble_prime(resolve_project_root()))


@mcp.tool()
def prime_applicable_lore(encounter: str, campaign: str | None = None) -> list[dict[str, Any]]:
    """Resolve the enabled lore set applicable to an encounter: world-assigned lore union
    lore assigned to the encounter's region(s). Returns name/summary/ref entries for
    selective hydration - `ref` is the lore name. Campaign defaults to the active (open)
    campaign when omitted."""
    root = resolve_project_root()
    resolved_campaign = campaign_core.resolve_campaign(root, campaign, require_mutable=False)
    entries = prime_core.applicable_lore(root, resolved_campaign, encounter)
    return [{"name": entry.name, "summary": entry.summary, "ref": entry.ref} for entry in entries]
