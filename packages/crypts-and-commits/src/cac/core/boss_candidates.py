"""Read-only, local-record eligibility and bounded discovery of boss goals."""

import json
from collections import deque
from pathlib import Path
from typing import Any

import yaml

from cac.core import boss, budget, campaign, config, coupling, references
from cac.core.frontmatter_utils import SUMMARY_ABSENT_MESSAGE

_DETAIL_LIMIT = 16


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _order(name: str) -> tuple[int, int, str]:
    match = config.BOSS_NUMBER_PATTERN.fullmatch(name)
    return (0, int(match[1]), name) if match else (1, 0, name)


def _issue(name: str, code: str, message: str, **context: Any) -> dict[str, Any]:
    return {"name": name, "code": code, "message": message, **context}


def _campaign_context(root: Path, name: str, record: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    linked = record.get("campaign")
    if linked is None:
        return {}, []
    context = {"campaign": linked, "campaign_status": None}
    try:
        campaign.validate_name(linked)
        live = boss._safe_path(root, campaign.campaign_dir(root) / f"{linked}.md")
        archived = boss._safe_path(root, campaign.archive_campaign_dir(root) / f"{linked}.md")
        if live.exists() and archived.exists():
            return context, [
                _issue(name, "ambiguous_campaign", "Linked campaign exists live and archived.", campaign=linked)
            ]
        if not live.exists() and not archived.exists():
            return context, [_issue(name, "campaign_not_found", "Linked campaign is missing.", campaign=linked)]
        metadata, _ = campaign.read_metadata(root, linked)
        is_archived = archived.exists()
        if (
            metadata.get("name") != linked
            or metadata.get("status", "draft") not in config.CAMPAIGN_STATUSES
            or type(metadata.get("archived", False)) is not bool
            or metadata.get("archived", False) != is_archived
        ):
            return context, [
                _issue(
                    name,
                    "invalid_campaign_record",
                    "Linked campaign metadata/location is inconsistent.",
                    campaign=linked,
                )
            ]
        context["campaign_status"] = metadata.get("status", "draft")
        issues = []
        from cac.core import campaign_bosses

        if name not in campaign_bosses.read(metadata):
            issues.append(
                _issue(
                    name,
                    "campaign_boss_mismatch",
                    "Linked campaign does not reciprocally reference this boss.",
                    campaign=linked,
                )
            )
        expected = {"available": ("draft", "open", "paused"), "vanquished": ("completed",)}
        if (
            metadata.get("status", "draft") not in expected.get(record["status"], ())
            or record.get("archived", False) != is_archived
        ):
            issues.append(
                _issue(
                    name,
                    "campaign_state_mismatch",
                    "Boss and linked campaign lifecycle/archive states disagree.",
                    campaign=linked,
                )
            )
        return context, issues
    except (ValueError, OSError, TypeError, yaml.YAMLError):
        return context, [
            _issue(
                name,
                "invalid_campaign_link",
                "Cannot safely read the linked campaign; inspect its name, storage, and metadata.",
                campaign=linked,
            )
        ]


def _snapshot(root: Path) -> tuple[dict, dict, dict, dict, list[str]]:
    names = sorted(boss.list_bosses(root, include_archived=True), key=_order)
    known = set(names)
    live = boss.list_bosses(root)
    records, edges, issues, contexts = {}, {}, {}, {}
    for name in names:
        edges[name], issues[name], contexts[name] = [], [], {}
        try:
            record, _ = boss.read_metadata(root, name)
        except (ValueError, OSError, TypeError, yaml.YAMLError):
            issues[name].append(
                _issue(
                    name,
                    "invalid_record",
                    "Cannot read boss metadata safely; inspect name, status, provenance, archive flag, and storage.",
                )
            )
            continue
        records[name] = record
        summary = record.get("summary", SUMMARY_ABSENT_MESSAGE)
        if not isinstance(summary, str) or len(summary) > config.SUMMARY_MAX_LENGTH:
            issues[name].append(
                _issue(name, "invalid_summary", "Boss summary must be text within the routing-summary length cap.")
            )
        contexts[name], link_issues = _campaign_context(root, name, record)
        issues[name].extend(link_issues)
        dependencies = record.get("depends_on", [])
        if not isinstance(dependencies, list):
            issues[name].append(
                _issue(name, "invalid_dependencies", "depends_on must be a list of canonical boss names.")
            )
            continue
        seen = set()
        for target in dependencies:
            try:
                boss.validate_name(target)
            except boss.BossError:
                issues[name].append(
                    _issue(name, "invalid_dependencies", "A prerequisite entry is not a valid canonical boss name.")
                )
                continue
            if target in seen:
                issues[name].append(
                    _issue(name, "duplicate_dependency", "Duplicate prerequisite edge.", prerequisite=target)
                )
                continue
            seen.add(target)
            edges[name].append(target)
            if target == name:
                issues[name].append(_issue(name, "self_dependency", "Boss depends on itself.", prerequisite=target))
            if target not in known:
                issues[name].append(
                    _issue(name, "missing_prerequisite", "Prerequisite record is missing.", prerequisite=target)
                )
    for name, diagnostics in coupling.boss_diagnostics(root, records).items():
        issues.setdefault(name, []).extend(diagnostics)
    return records, edges, issues, contexts, live


def _damaged_graph(edges: dict[str, list[str]], issues: dict[str, list[dict]]) -> set[str]:
    """Peel acyclic leaves, then propagate integrity failures to dependents iteratively."""
    dependents: dict[str, list[str]] = {name: [] for name in edges}
    remaining = {}
    for name, targets in edges.items():
        remaining[name] = sum(target in edges for target in targets)
        for target in targets:
            if target in edges:
                dependents[target].append(name)
    queue = deque(name for name in edges if remaining[name] == 0)
    while queue:
        for dependent in dependents[queue.popleft()]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                queue.append(dependent)
    for name in edges:
        if remaining[name]:
            issues[name].append(
                _issue(name, "dependency_cycle", "The prerequisite graph reachable from this boss contains a cycle.")
            )
    damaged = {name for name in edges if issues[name]}
    queue = deque(damaged)
    while queue:
        for dependent in dependents[queue.popleft()]:
            if dependent not in damaged:
                damaged.add(dependent)
                queue.append(dependent)
    return damaged


def _evaluate(root: Path) -> tuple[list[dict], dict[str, int], list[dict]]:
    records, edges, issues, contexts, live = _snapshot(root)
    damaged = _damaged_graph(edges, issues)
    counts = {
        "total_live": len(live),
        "total_archived": len(edges) - len(live),
        "pool": 0,
        "eligible": 0,
        "blocked": 0,
        "not_ready": 0,
        "excluded": 0,
        "invalid": 0,
    }
    items = []
    inventory = references.Inventory(root)
    for name in sorted(live, key=_order):
        record = records.get(name)
        if record is None:
            counts["invalid"] += 1
            continue
        if record["status"] not in ("proposed", "available") or record.get("campaign") is not None:
            counts["excluded"] += 1
            continue
        prerequisites, diagnostics = [], issues[name].copy()
        for target in edges[name]:
            prerequisite = records.get(target, {})
            satisfied = prerequisite.get("status") == "vanquished" and target not in damaged
            prerequisites.append(
                {
                    "name": target,
                    "status": prerequisite.get("status"),
                    "archived": prerequisite.get("archived"),
                    "satisfied": satisfied,
                    **(
                        {
                            "completion_origin": "roadmap",
                            "ref": "boss_get",
                        }
                        if prerequisite.get("status") == "vanquished"
                        and prerequisite.get("provenance", {}).get("progress") == "completed"
                        else {}
                    ),
                    **contexts.get(target, {}),
                }
            )
            if target in damaged:
                diagnostics.append(
                    _issue(
                        name,
                        "dependency_integrity",
                        "Prerequisite has reachable integrity errors; inspect that boss.",
                        prerequisite=target,
                    )
                )
        unsatisfied = sum(not entry["satisfied"] for entry in prerequisites)
        classification = (
            "not_ready"
            if record["status"] == "proposed"
            else "blocked"
            if unsatisfied or name in damaged
            else "eligible"
        )
        reasons = []
        if classification == "not_ready":
            reasons.append("not_ready")
        if unsatisfied:
            reasons.append("prerequisite_unsatisfied")
        if name in damaged:
            reasons.append("integrity_error")
        summary = record.get("summary") or SUMMARY_ABSENT_MESSAGE
        items.append(
            {
                "name": name,
                "identity": inventory.identity("boss", name),
                "summary": summary if isinstance(summary, str) else SUMMARY_ABSENT_MESSAGE,
                "status": record["status"],
                **(
                    {
                        "roadmap": {
                            "recorded_progress": record["provenance"]["progress"],
                            "source": record["provenance"]["source"][:120],
                            "source_truncated": len(record["provenance"]["source"]) > 120,
                            "ref": "boss_get",
                        }
                    }
                    if "provenance" in record
                    else {}
                ),
                "classification": classification,
                "eligible": classification == "eligible",
                "reason_codes": reasons,
                "prerequisite_count": len(prerequisites),
                "unsatisfied_count": unsatisfied,
                "diagnostic_count": len(diagnostics),
                "prerequisites": prerequisites,
                "diagnostics": diagnostics,
                "ref": "boss_get",
            }
        )
        counts["pool"] += 1
        counts[classification] += 1
    diagnostics = [entry for name in sorted(issues, key=_order) for entry in issues[name]]
    return items, counts, diagnostics


def _bounded_item(item: dict, limit: int, *, minimal: bool = False) -> dict:
    result = {
        **item,
        "summary": "" if minimal else item["summary"][: config.SUMMARY_MAX_LENGTH],
        "prerequisites": [] if minimal else item["prerequisites"][:_DETAIL_LIMIT],
        "diagnostics": [] if minimal else item["diagnostics"][:_DETAIL_LIMIT],
    }
    if minimal and "roadmap" in result:
        result["roadmap"] = {**result["roadmap"], "source": "", "source_truncated": True}
    while True:
        result["summary_truncated"] = result["summary"] != item["summary"]
        result["prerequisites_omitted"] = item["prerequisite_count"] - len(result["prerequisites"])
        result["diagnostics_omitted"] = item["diagnostic_count"] - len(result["diagnostics"])
        excess = len(_json(result)) - limit
        if excess <= 0 or minimal:
            return result
        if result["diagnostics"]:
            result["diagnostics"] = result["diagnostics"][: len(result["diagnostics"]) // 2]
        elif result["prerequisites"]:
            result["prerequisites"] = result["prerequisites"][: len(result["prerequisites"]) // 2]
        elif result["summary"]:
            result["summary"] = result["summary"][: max(0, len(result["summary"]) - excess)]
        elif result.get("roadmap", {}).get("source"):
            result["roadmap"] = {**result["roadmap"], "source": "", "source_truncated": True}
        else:
            raise boss.BossError(
                "Candidate identifiers and required fields exceed the response budget; increase it or inspect with boss_get."
            )


def candidates(root: Path, cursor: str | None = None) -> dict[str, Any]:
    """Return a serialized-budget page of local candidate summaries and integrity diagnostics."""
    items, counts, diagnostics = _evaluate(root)
    # Validate cursors using the shared contract even for an empty collection.
    budget.paginate(items, cursor, budget=1, render=_json)
    limit = config.RESPONSE_BUDGET
    result = {
        "items": [],
        "next_cursor": str(len(items)) if items else None,
        "counts": counts,
        "healthy": not diagnostics,
        "diagnostics": [],
        "diagnostics_omitted": len(diagnostics),
        "diagnostics_ref": "boss_list" if diagnostics else None,
    }
    minimum = max((len(_json(_bounded_item(item, limit, minimal=True))) + 1 for item in items), default=0)
    if len(_json(result)) + minimum > limit:
        raise boss.BossError(
            "Candidate envelope/identifiers exceed the response budget; increase it or inspect with boss_list/boss_get."
        )
    diagnostic_budget = min(limit // 4, limit - len(_json(result)) - minimum)
    used = 0
    for entry in diagnostics[:_DETAIL_LIMIT]:
        cost = len(_json(entry)) + 1
        if used + cost > diagnostic_budget:
            break
        result["diagnostics"].append(entry)
        used += cost
    result["diagnostics_omitted"] = len(diagnostics) - len(result["diagnostics"])
    item_budget = limit - len(_json(result))
    bounded = [_bounded_item(item, item_budget) for item in items]
    page = budget.paginate(bounded, cursor, budget=item_budget, render=_json)
    result["items"], result["next_cursor"] = page.items, page.next_cursor
    return result


def assess(root: Path, name: str) -> dict:
    """Untruncated eligibility shared by discovery and first assignment."""
    items, _, _ = _evaluate(root)
    for item in items:
        if item["name"] == name:
            return item
    raise boss.BossError(f"Boss {name!r} is not in the live unassigned planning pool.")
