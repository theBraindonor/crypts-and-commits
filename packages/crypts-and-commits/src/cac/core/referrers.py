"""Referrer inventory for guarded deletes: lore, regions and campaigns refuse while referenced.

Every link list that can name a lore entry, region or campaign is read here, so a delete can list
every referrer instead of leaving dangling names behind. Referrers render as
`<type> <canonical name> (<field>)` and sort by type, then name.
"""

from pathlib import Path

import frontmatter


class ReferencedRecordError(ValueError):
    """Raised when deleting a record that other records still reference."""


def _sorted(entries: list[tuple[str, str, str]]) -> list[str]:
    return [f"{kind} {name} ({field})" if name else f"{kind} ({field})" for kind, name, field in sorted(set(entries))]


def lore_referrers(root: Path, name: str) -> list[str]:
    """World and regions whose `assigned_lore` names this lore entry."""
    from cac.core import region, world

    entries = []
    path = world.world_path(root)
    if path.exists() and name in (frontmatter.load(path).get(world.ASSIGNED_LORE_KEY) or []):
        entries.append(("world", "", world.ASSIGNED_LORE_KEY))
    for region_name in region.list_regions(root):
        metadata, _ = region.read_metadata(root, region_name)
        if name in (metadata.get(region.ASSIGNED_LORE_KEY) or []):
            entries.append(("region", region_name, region.ASSIGNED_LORE_KEY))
    return _sorted(entries)


def region_referrers(root: Path, name: str) -> list[str]:
    """Lore whose `assigned_regions` names this region, plus unarchived encounters (any status, any
    live campaign) whose `regions` name it. Archived campaigns' encounters are history."""
    from cac.core import campaign, encounter, lore

    entries = []
    for lore_name in lore.list_lore(root):
        metadata, _ = lore.read_metadata(root, lore_name)
        if name in (metadata.get(lore.ASSIGNED_REGIONS_KEY) or []):
            entries.append(("lore", lore_name, lore.ASSIGNED_REGIONS_KEY))
    for campaign_name in campaign.list_campaigns(root):
        directory = encounter.encounter_dir(root, campaign_name)
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.md")):
            if name in (frontmatter.load(path).get(encounter.REGIONS_KEY) or []):
                entries.append(("encounter", f"{campaign_name}/{path.stem}", encounter.REGIONS_KEY))
    return _sorted(entries)


def campaign_referrers(root: Path, name: str) -> list[str]:
    """The campaign's own encounters, live or archived, and every ruling, live or archived, whose
    `campaign` names it. Boss links are guarded separately by coupling's campaign delete guard."""
    from cac.core import encounter, ruling, world

    entries = []
    for directory in (encounter.encounter_dir(root, name), encounter.archive_encounter_dir(root, name)):
        if directory.is_dir():
            entries.extend(("encounter", f"{name}/{path.stem}", "campaign") for path in directory.glob("*.md"))
    if world.world_path(root).exists():
        for ruling_name in ruling.list_rulings(root, include_archived=True):
            metadata, _ = ruling.read_metadata(root, ruling_name)
            if metadata.get("campaign") == name:
                entries.append(("ruling", ruling_name, "campaign"))
    return _sorted(entries)


def ensure_unreferenced(kind: str, name: str, referrers: list[str]) -> None:
    """Raise listing every referrer; a delete must not leave dangling references behind."""
    if referrers:
        raise ReferencedRecordError(
            f"Cannot delete {kind} {name!r}: it is still referenced by {', '.join(referrers)}. "
            "Unassign or remove these references first."
        )
