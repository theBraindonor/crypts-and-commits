import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import frontmatter
import yaml

from cac.core import boss, campaign_bosses, config, coupling
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
    active_bosses: list[dict] = field(default_factory=list)
    active_boss_diagnostics: list[dict] = field(default_factory=list)
    active_boss_names: list[str] = field(default_factory=list)


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
    campaign_body = (
        frontmatter.load(campaign_core.campaign_path(root, active_campaign)).content if active_campaign else None
    )
    names, goals, diagnostics = _active_bosses(root, active_campaign)
    return PrimeBundle(
        world=world,
        world_lore=world_lore,
        regions=regions,
        active_campaign=active_campaign,
        campaign_body=campaign_body,
        active_bosses=goals,
        active_boss_diagnostics=diagnostics,
        active_boss_names=names,
    )


def _active_bosses(root: Path, campaign: str | None) -> tuple[list[str], list[dict], list[dict]]:
    if campaign is None:
        return [], [], []
    names, goals, diagnostics = [], [], []

    def diagnostic(member, error):
        return {"code": "invalid_boss_link", "campaign": campaign, "boss": member, "message": str(error)[:300]}

    try:
        post = frontmatter.load(campaign_core.campaign_path(root, campaign))
        names = campaign_bosses.read(post.metadata)
        links = coupling.Links(root)
        if not names:
            links.current(campaign)
        for member in names:
            try:
                links._pair(member, campaign)
                metadata, body = boss.read_metadata(root, member)
                goals.append(
                    {
                        "metadata": {
                            key: metadata.get(key) for key in ("name", "status", "archived", "depends_on", "campaign")
                        },
                        "summary": metadata.get("summary", ""),
                        "body": body,
                    }
                )
            except (ValueError, OSError, TypeError, KeyError, yaml.YAMLError) as error:
                diagnostics.append(diagnostic(member, error))
    except (ValueError, OSError, TypeError, KeyError, yaml.YAMLError) as error:
        diagnostics.append(diagnostic(None, error))
    return names, goals, diagnostics


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
    for index, goal in enumerate(result["active_bosses"]):
        fields.append(
            (
                f"active_bosses[{index}].body",
                goal,
                "body",
                {"tool": "boss_get", "name": goal["metadata"]["name"]},
            )
        )
    originals = []
    for field_name, owner, key, ref in fields:
        text = owner[key]
        if text:
            notice = {"field": field_name, "notice": "TRUNCATED", "ref": ref}
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
