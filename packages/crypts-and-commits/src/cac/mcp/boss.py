from typing import Any

from cac.core import boss as boss_core
from cac.core import boss_candidates as candidates_core
from cac.core import budget as budget_core
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp


@mcp.tool()
def boss_candidates(cursor: str | None = None) -> dict[str, Any]:
    """Page local boss summaries, readiness/eligibility, blockers, and integrity diagnostics. Read-only; no proof of integration."""
    return candidates_core.candidates(resolve_project_root(), cursor)


@mcp.tool()
def boss_get(name: str) -> dict[str, Any]:
    """Read live or archived boss metadata, routing summary, and budgeted body."""
    root = resolve_project_root()
    metadata, body = boss_core.read_metadata(root, name)
    summary = metadata.pop("summary", "")
    return {
        "metadata": metadata,
        "summary": summary,
        "body": budget_core.truncate_body(body, boss_core.boss_path(root, name)),
    }


@mcp.tool()
def boss_list(cursor: str | None = None, include_archived: bool = False) -> dict[str, Any]:
    """Page canonical names, optionally including archived allocations. Order is not priority."""
    names = boss_core.list_bosses(resolve_project_root(), include_archived=include_archived)
    page = budget_core.paginate(names, cursor)
    return {"items": page.items, "next_cursor": page.next_cursor}


@mcp.tool()
def boss_create(name: str, body: str, summary: str) -> dict[str, Any]:
    """create boss planning body and routing summary (maximum 500 characters) together."""
    boss_core.create_boss(resolve_project_root(), name, body, summary)
    return boss_get(name)


@mcp.tool()
def boss_update(name: str, body: str, summary: str) -> dict[str, Any]:
    """update boss planning body and routing summary (maximum 500 characters) together."""
    boss_core.update_boss(resolve_project_root(), name, body, summary)
    return boss_get(name)


@mcp.tool()
def boss_make_available(name: str) -> dict[str, Any]:
    """Mark an unassigned proposed boss available; prerequisites need not be satisfied."""
    boss_core.make_available(resolve_project_root(), name)
    return boss_get(name)


@mcp.tool()
def boss_withdraw(name: str) -> dict[str, Any]:
    """Withdraw an unassigned proposed/available boss, preserving incoming dependencies."""
    boss_core.withdraw(resolve_project_root(), name)
    return boss_get(name)


@mcp.tool()
def boss_reactivate(name: str) -> dict[str, Any]:
    """Return an unarchived, unassigned withdrawn boss to proposed."""
    boss_core.reactivate(resolve_project_root(), name)
    return boss_get(name)


@mcp.tool()
def boss_archive(name: str) -> dict[str, Any]:
    """Archive an unassigned withdrawn boss; retain its name and status."""
    boss_core.archive_boss(resolve_project_root(), name)
    return boss_get(name)


@mcp.tool()
def boss_assign_dependency(name: str, dependency: str) -> dict[str, Any]:
    """assign a direct canonical boss prerequisite, validating graph integrity before writes."""
    boss_core.assign_dependency(resolve_project_root(), name, dependency)
    return boss_get(name)


@mcp.tool()
def boss_unassign_dependency(name: str, dependency: str) -> dict[str, Any]:
    """unassign a direct canonical boss prerequisite, validating graph integrity before writes."""
    boss_core.unassign_dependency(resolve_project_root(), name, dependency)
    return boss_get(name)
