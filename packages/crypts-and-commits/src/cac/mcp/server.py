from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from cac.core import campaign as campaign_core
from cac.core import prime as prime_core
from cac.core import world as world_core

mcp = FastMCP("cac")


def _world_to_dict(world: world_core.World) -> dict[str, Any]:
    return {"metadata": world.metadata, "body": world.body}


@mcp.tool()
def world_get() -> dict[str, Any]:
    """Show the current world summary and its frontmatter attributes."""
    return _world_to_dict(world_core.read_world(Path.cwd()))


@mcp.tool()
def world_set(key: str, value: str) -> dict[str, Any]:
    """Set a frontmatter attribute on the world file."""
    return _world_to_dict(world_core.set_attribute(Path.cwd(), key, value))


@mcp.tool()
def world_set_body(body: str) -> dict[str, Any]:
    """Replace the world summary body text."""
    return _world_to_dict(world_core.update_body(Path.cwd(), body))


def _prime_bundle_to_dict(bundle: prime_core.PrimeBundle) -> dict[str, Any]:
    return {
        "world": _world_to_dict(bundle.world),
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
    return _prime_bundle_to_dict(prime_core.assemble_prime(Path.cwd()))


@mcp.tool()
def prime_applicable_lore(encounter: str, campaign: str | None = None) -> list[dict[str, Any]]:
    """Resolve the enabled lore set applicable to an encounter: world-assigned lore union
    lore assigned to the encounter's region(s). Returns name/summary/ref entries for
    selective hydration - `ref` is the lore name. Campaign defaults to the active (open)
    campaign when omitted."""
    root = Path.cwd()
    resolved_campaign = campaign_core.resolve_campaign(root, campaign, require_mutable=False)
    entries = prime_core.applicable_lore(root, resolved_campaign, encounter)
    return [{"name": entry.name, "summary": entry.summary, "ref": entry.ref} for entry in entries]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
