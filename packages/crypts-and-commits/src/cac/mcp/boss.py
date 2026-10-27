from typing import Any

from cac.core import boss as boss_core
from cac.core import boss_candidates as candidates_core
from cac.core import references
from cac.core.paths import resolve_project_root
from cac.mcp.instance import mcp


@mcp.tool()
@references.inputs("boss")
def boss_candidates(cursor: str | None = None) -> dict[str, Any]:
    """Page local boss summaries, readiness/eligibility, blockers, and integrity diagnostics. Read-only; no proof of integration."""
    return candidates_core.candidates(resolve_project_root(), cursor)


@mcp.tool()
@references.inputs("boss")
def boss_get(name: str) -> dict[str, Any]:
    """Read a boss by canonical name or numbered short reference."""
    return _read_boss(name)


@mcp.tool()
@references.inputs("boss")
def boss_list(cursor: str | None = None, include_archived: bool = False) -> dict[str, Any]:
    """Page canonical names, optionally including archived allocations. Order is not priority."""
    names = boss_core.list_bosses(resolve_project_root(), include_archived=include_archived)
    return references.identity_page(resolve_project_root(), "boss", names, cursor)


@mcp.tool()
@references.inputs("boss", create=True)
def boss_create(name: str, body: str, summary: str) -> dict[str, Any]:
    """create boss planning body and routing summary (maximum 500 characters) together."""
    boss_core.create_boss(resolve_project_root(), name, body, summary)
    return _read_boss(name)


@mcp.tool()
@references.inputs("boss")
def boss_update(name: str, body: str, summary: str) -> dict[str, Any]:
    """update boss planning body and routing summary (maximum 500 characters) together."""
    boss_core.update_boss(resolve_project_root(), name, body, summary)
    return _read_boss(name)


@mcp.tool()
@references.inputs("boss")
def boss_make_available(name: str) -> dict[str, Any]:
    """Mark an unassigned proposed boss available; prerequisites need not be satisfied."""
    boss_core.make_available(resolve_project_root(), name)
    return _read_boss(name)


@mcp.tool()
@references.inputs("boss")
def boss_withdraw(name: str) -> dict[str, Any]:
    """Withdraw an unassigned proposed/available boss, preserving incoming dependencies."""
    boss_core.withdraw(resolve_project_root(), name)
    return _read_boss(name)


@mcp.tool()
@references.inputs("boss")
def boss_reactivate(name: str) -> dict[str, Any]:
    """Return an unarchived, unassigned withdrawn boss to proposed."""
    boss_core.reactivate(resolve_project_root(), name)
    return _read_boss(name)


@mcp.tool()
@references.inputs("boss")
def boss_archive(name: str) -> dict[str, Any]:
    """Archive an unassigned withdrawn boss; retain its name and status."""
    boss_core.archive_boss(resolve_project_root(), name)
    return _read_boss(name)


@mcp.tool()
@references.inputs("boss")
def boss_assign_dependency(name: str, dependency: str) -> dict[str, Any]:
    """assign a direct canonical boss prerequisite, validating graph integrity before writes."""
    boss_core.assign_dependency(resolve_project_root(), name, dependency)
    return _read_boss(name)


@mcp.tool()
@references.inputs("boss", remove=True)
def boss_unassign_dependency(name: str, dependency: str) -> dict[str, Any]:
    """unassign a direct canonical boss prerequisite, validating graph integrity before writes."""
    boss_core.unassign_dependency(resolve_project_root(), name, dependency)
    return _read_boss(name)


def _read_boss(name: str) -> dict[str, Any]:
    root = resolve_project_root()
    metadata, body = boss_core.read_metadata(root, name)
    summary = metadata.pop("summary", "")
    return {"metadata": metadata, "summary": summary, "body": body}
