from pathlib import Path

from cac.core import campaign as campaign_core
from cac.core import encounter as encounter_core
from langchain_core.tools import BaseTool, tool


def build_tools(root: Path) -> list[BaseTool]:
    def list_encounters(campaign: str | None = None) -> list[str]:
        """List encounter names within a campaign, oldest-updated first. Omit campaign to use
        the currently active (open) campaign."""
        resolved = campaign_core.resolve_campaign(root, campaign, require_mutable=False)
        return encounter_core.list_encounters(root, resolved)

    def get_encounter(name: str, campaign: str | None = None) -> dict:
        """Get an encounter's status, regions, dependencies, and full body by name. Omit
        campaign to use the currently active (open) campaign."""
        resolved = campaign_core.resolve_campaign(root, campaign, require_mutable=False)
        encounter = encounter_core.read_encounter(root, resolved, name)
        return {
            "name": encounter.name,
            "campaign": encounter.campaign,
            "status": encounter.status,
            "regions": encounter.regions,
            "depends_on": encounter.depends_on,
            "body": encounter.body,
        }

    return [tool(list_encounters), tool(get_encounter)]
