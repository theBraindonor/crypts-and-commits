import json
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from cac.core import boss, config, coupling
from cac.core import campaign as campaign_core
from cac.core import encounter as encounter_core
from cac.core import lore as lore_core
from cac.core import region as region_core
from cac.core import world as world_core
from cac.core.world import World

_ENABLED_KEY = "enabled"


@dataclass(frozen=True)
class LoreSummary:
    name: str
    summary: str


@dataclass(frozen=True)
class RegionEntry:
    name: str
    summary: str
    path: str
    assigned_lore: list[str]


@dataclass(frozen=True)
class PrimeBundle:
    world: World
    world_lore: list[LoreSummary]
    regions: list[RegionEntry]
    active_campaign: str | None
    campaign_body: str | None
    active_boss: dict | None = None
    active_boss_diagnostic: dict | None = None


@dataclass(frozen=True)
class ApplicableLoreEntry:
    name: str
    summary: str
    ref: str


def assemble_prime(root: Path) -> PrimeBundle:
    """Assemble the global prime bundle: world (full) + world-assigned enabled lore
    (summaries) + region map (summary + path + assigned-lore edge names per region) +
    active campaign and linked boss (full bodies, not recursive collections)."""
    world = world_core.read_world(root)
    world_lore = _enabled_lore_summaries(root, world.metadata.get(world_core.ASSIGNED_LORE_KEY, []) or [])
    regions = [_region_entry(root, name) for name in region_core.list_regions(root)]
    active_campaign = campaign_core.active_campaign(root)
    campaign_body = campaign_core.read_campaign(root, active_campaign).body if active_campaign else None
    active_boss, diagnostic = _active_boss(root, active_campaign)
    return PrimeBundle(
        world=world,
        world_lore=world_lore,
        regions=regions,
        active_campaign=active_campaign,
        campaign_body=campaign_body,
        active_boss=active_boss,
        active_boss_diagnostic=diagnostic,
    )


def _active_boss(root: Path, campaign: str | None) -> tuple[dict | None, dict | None]:
    if campaign is None:
        return None, None
    origin = None
    try:
        metadata, _ = campaign_core.read_metadata(root, campaign)
        origin = metadata.get("boss")
        links = coupling.Links(root)
        current = links.current(campaign)
        if current is None:
            return None, None
        metadata, body = boss.read_metadata(root, current)
        return {
            "metadata": {key: metadata.get(key) for key in ("name", "status", "archived", "depends_on", "campaign")},
            "summary": metadata.get("summary", ""),
            "body": body,
        }, None
    except (ValueError, OSError, TypeError, KeyError, yaml.YAMLError) as error:
        return None, {
            "code": "invalid_boss_link",
            "campaign": campaign,
            "boss": origin if isinstance(origin, str) else repr(origin)[:200] if origin is not None else None,
            "message": str(error)[:300],
        }


def present(bundle: PrimeBundle) -> dict:
    """One serialized budget for both surfaces; raw in-process context stays intact."""
    result = asdict(bundle)
    result["truncations"] = []

    def size() -> int:
        return len(json.dumps(result, ensure_ascii=False, default=str, separators=(",", ":")))

    if size() <= config.RESPONSE_BUDGET:
        return result
    fields = [("world.body", result["world"], "body", {"tool": "world_get"})]
    if bundle.campaign_body is not None:
        fields.append(
            ("campaign_body", result, "campaign_body", {"tool": "campaign_get", "name": bundle.active_campaign})
        )
    if bundle.active_boss is not None:
        fields.append(
            (
                "active_boss.body",
                result["active_boss"],
                "body",
                {"tool": "boss_get", "name": bundle.active_boss["metadata"]["name"]},
            )
        )
    originals = []
    for field, owner, key, ref in fields:
        text = owner[key]
        if text:
            notice = {"field": field, "notice": "TRUNCATED", "ref": ref}
            result["truncations"].append(notice)
            originals.append((owner, key, text, notice))
            owner[key] = ""
    if size() > config.RESPONSE_BUDGET:
        raise ValueError("Prime routing metadata/state exceeds the response budget; increase it.")
    for index, (owner, key, text, notice) in enumerate(originals):
        allowance = (config.RESPONSE_BUDGET - size()) // (len(originals) - index)
        baseline = size()
        low, high = 0, len(text)
        while low < high:
            middle = (low + high + 1) // 2
            owner[key] = text[:middle]
            if size() - baseline <= allowance:
                low = middle
            else:
                high = middle - 1
        owner[key] = text[:low]
        if low == len(text):
            result["truncations"].remove(notice)
    return result


def applicable_lore(root: Path, campaign: str, encounter_name: str) -> list[ApplicableLoreEntry]:
    """Resolve the enabled lore that applies to an encounter: world-assigned lore union
    lore assigned to any of the encounter's regions. Returned as name/summary/ref entries
    for selective hydration (`ref` is the lore name; hydrate the full body via
    `cac lore get <ref>`)."""
    encounter = encounter_core.read_encounter(root, campaign, encounter_name)
    world = world_core.read_world(root)
    names = set(world.metadata.get(world_core.ASSIGNED_LORE_KEY, []) or [])
    for region_name in encounter.regions:
        metadata, _ = region_core.read_metadata(root, region_name)
        names.update(metadata.get(region_core.ASSIGNED_LORE_KEY, []) or [])
    return [
        ApplicableLoreEntry(name=summary.name, summary=summary.summary, ref=summary.name)
        for summary in _enabled_lore_summaries(root, names)
    ]


def _enabled_lore_summaries(root: Path, names: set[str] | list[str]) -> list[LoreSummary]:
    result = []
    for name in sorted(names):
        metadata, _ = lore_core.read_metadata(root, name)
        if not metadata.get(_ENABLED_KEY, False):
            continue
        result.append(LoreSummary(name=name, summary=lore_core.read_summary(root, name)))
    return result


def _region_entry(root: Path, name: str) -> RegionEntry:
    metadata, _ = region_core.read_metadata(root, name)
    summary = region_core.read_summary(root, name)
    return RegionEntry(
        name=name,
        summary=summary,
        path=metadata.get("path", ""),
        assigned_lore=sorted(metadata.get(region_core.ASSIGNED_LORE_KEY, []) or []),
    )
