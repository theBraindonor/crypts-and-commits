from pathlib import Path

from cac.core import prime as prime_core


def render_context_priming(root: Path) -> str:
    bundle = prime_core.assemble_prime(root)

    lines = [f"# {bundle.world.metadata.get('name', 'Project')}", "", bundle.world.body.strip()]

    if bundle.world_lore:
        lines += ["", "## Global lore"]
        lines += [f"- {entry.name}: {entry.summary}" for entry in bundle.world_lore]

    if bundle.regions:
        lines += ["", "## Regions"]
        lines += [f"- {region.name} ({region.path}): {region.summary}" for region in bundle.regions]

    if bundle.active_campaign and bundle.campaign_body:
        lines += ["", f"## Active campaign: {bundle.active_campaign}", "", bundle.campaign_body.strip()]

    return "\n".join(lines)
