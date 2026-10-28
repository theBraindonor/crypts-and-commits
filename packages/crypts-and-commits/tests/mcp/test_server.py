import asyncio

from cac.mcp.instance import mcp
from cac.mcp.server import main  # noqa: F401  -- import triggers world/prime registration


def test_all_domain_tools_are_registered() -> None:
    tools = asyncio.run(mcp.list_tools())
    tool_names = {tool.name for tool in tools}

    assert tool_names == {
        "rumors_list",
        "rumors_get",
        "rumors_create",
        "rumors_update",
        "rumors_delete",
        "boss_create",
        "boss_record",
        "boss_candidates",
        "boss_assign_campaign",
        "boss_get",
        "boss_list",
        "boss_update",
        "boss_make_available",
        "boss_withdraw",
        "boss_reactivate",
        "boss_archive",
        "boss_assign_dependency",
        "boss_unassign_dependency",
        "world_get",
        "world_set",
        "world_set_body",
        "prime_get",
        "prime_applicable_lore",
        "lore_get",
        "lore_list",
        "lore_create",
        "lore_update",
        "lore_delete",
        "lore_set_summary",
        "lore_assign_world",
        "lore_unassign_world",
        "lore_assign_region",
        "lore_unassign_region",
        "lore_enable",
        "lore_disable",
        "region_get",
        "region_list",
        "region_create",
        "region_update",
        "region_delete",
        "region_set_summary",
        "region_set_path",
        "campaign_get",
        "campaign_list",
        "campaign_create",
        "campaign_set_bosses",
        "campaign_update",
        "campaign_delete",
        "campaign_open",
        "campaign_pause",
        "campaign_complete",
        "campaign_abandon",
        "campaign_archive",
        "campaign_reactivate",
        "encounter_get",
        "encounter_list",
        "encounter_order",
        "encounter_create",
        "encounter_update",
        "encounter_delete",
        "encounter_review",
        "encounter_open",
        "encounter_record_message",
        "encounter_complete",
        "encounter_abandon",
        "encounter_assign_region",
        "encounter_unassign_region",
        "encounter_assign_dependency",
        "encounter_unassign_dependency",
        "index_status",
        "index_search",
        "docs_list",
        "docs_get",
    }


def test_domain_get_tools_accept_continuation_cursor() -> None:
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    for name in ("world_get", "lore_get", "region_get", "campaign_get", "boss_get", "encounter_get", "rumors_get"):
        assert "cursor" in tools[name].input_schema["properties"], name
