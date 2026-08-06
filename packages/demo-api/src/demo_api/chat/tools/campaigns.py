from pathlib import Path

from cac.core import campaign as campaign_core
from langchain_core.tools import BaseTool, tool


def build_tools(root: Path) -> list[BaseTool]:
    def list_campaigns() -> list[dict]:
        """List all campaigns with their current status."""
        return [{"name": name, "status": status} for name, status in campaign_core.list_campaigns_with_status(root)]

    def get_campaign(name: str) -> dict:
        """Get a campaign's status and full body by name."""
        campaign = campaign_core.read_campaign(root, name)
        return {"name": campaign.name, "status": campaign.status, "body": campaign.body}

    return [tool(list_campaigns), tool(get_campaign)]
