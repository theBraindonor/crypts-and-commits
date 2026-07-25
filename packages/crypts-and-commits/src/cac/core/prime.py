from dataclasses import dataclass
from pathlib import Path

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


@dataclass(frozen=True)
class ApplicableLoreEntry:
    name: str
    summary: str
    ref: str


def assemble_prime(root: Path) -> PrimeBundle:
    """Assemble the global prime bundle: world (full) + world-assigned enabled lore
    (summaries) + region map (summary + path + assigned-lore edge names per region) +
    active campaign (full body, not its encounter list)."""
    world = world_core.read_world(root)
    world_lore = _enabled_lore_summaries(root, world.metadata.get(world_core.ASSIGNED_LORE_KEY, []) or [])
    regions = [_region_entry(root, name) for name in region_core.list_regions(root)]
    active_campaign = campaign_core.active_campaign(root)
    campaign_body = campaign_core.read_campaign(root, active_campaign).body if active_campaign else None
    return PrimeBundle(
        world=world,
        world_lore=world_lore,
        regions=regions,
        active_campaign=active_campaign,
        campaign_body=campaign_body,
    )


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
