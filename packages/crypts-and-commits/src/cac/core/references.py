"""External reference selection. Storage/domain routines keep exact canonical lookup.

Input matrix (the entry adapter uses this for every shipped CLI/MCP command):
boss/campaign targets: all get/update/lifecycle/archive/delete lookups; create is literal.
encounter targets: all get/update/delete/review/lifecycle/message/region/dependency lookups;
create is literal; campaign filters on list/order/create and applicable-lore use campaign refs.
dependency is scoped/canonicalized on assign/unassign only; region/lore/doc/text/cursor inputs
are untouched. There is no new resolver endpoint, allocation, or persistent cache.
"""

import json
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from inspect import signature
from pathlib import Path
from typing import Any

from cac.core import budget, config
from cac.core.paths import resolve_project_root, sourcebook_dir


class ReferenceError(ValueError):
    """Invalid or ambiguous external reference; no mutation may follow."""


class AmbiguousReferenceError(ReferenceError):
    """More than one retained identity matches the requested reference."""


def encoded(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class Inventory:
    """Request-local inventories. No stored reference is automatically reinterpreted."""

    def __init__(self, root: Path):
        self.root = root
        self.cache: dict[tuple[str, str | None], list[str]] = {}
        self.numeric: dict[tuple[str, str | None], dict[tuple[str, int], list[str]]] = {}

    def names(self, domain: str, campaign: str | None = None) -> list[str]:
        from cac.core import boss

        key = domain, campaign
        if key in self.cache:
            return self.cache[key]
        directory = {
            "boss": config.BOSS_DIR_NAME,
            "campaign": config.CAMPAIGN_DIR_NAME,
            "encounter": config.ENCOUNTER_DIR_NAME,
        }[domain]
        if domain == "encounter":
            self.validate(campaign)
        base = sourcebook_dir(self.root)
        live = base / directory
        archive = base / config.ARCHIVE_DIR_NAME / directory
        if domain == "encounter":
            live, archive = live / campaign, archive / campaign
        found = []
        for location in (live, archive):
            boss._safe_path(self.root, location / "_probe.md")
            if not location.exists():
                continue
            for path in sorted(location.glob("*.md")):
                boss._safe_path(self.root, path)
                self.validate(path.stem)
                if domain == "boss" and path.stem.lower() == "rumors":
                    raise ReferenceError("Reserved rumors namespace contains a boss record.")
                found.append(path.stem)
        duplicates = sorted(name for name, count in Counter(found).items() if count > 1)
        if duplicates:
            raise AmbiguousReferenceError(f"Ambiguous live/archive {domain} records: {', '.join(duplicates)}.")
        self.cache[key] = sorted(found)
        self.numeric[key] = {}
        for name in self.cache[key]:
            match = config.NUMBERED_NAME_PATTERN.fullmatch(name) or config.SHORT_REFERENCE_PATTERN.fullmatch(name)
            if match:
                self.numeric[key].setdefault((match[1], int(match[2])), []).append(name)
        return self.cache[key]

    @staticmethod
    def validate(value: str) -> None:
        if not isinstance(value, str) or not config.NAME_PATTERN.fullmatch(value) or value in config.RESERVED_NAMES:
            raise ReferenceError(f"Invalid reference {value!r}; use a canonical name or numbered short ref.")

    def resolve(self, domain: str, value: str, campaign: str | None = None, *, missing_literal: bool = False) -> str:
        self.validate(value)
        names = self.names(domain, campaign)
        short = config.SHORT_REFERENCE_PATTERN.fullmatch(value)
        prefix = {"boss": "b", "campaign": "c", "encounter": "e"}[domain]
        if short:
            if short[1] != prefix or int(short[2]) == 0:
                raise ReferenceError(f"Reference {value!r} is not a positive {domain} short ref.")
            number = int(short[2])
            matches = self.numeric[domain, campaign].get((prefix, number), [])
            if len(matches) > 1:
                raise AmbiguousReferenceError(
                    f"Ambiguous {domain} reference {value!r}: {', '.join(matches)}. Use a full canonical name."
                )
            if matches:
                return matches[0]
        elif value in names or missing_literal:
            return value
        # Preserve existing domain not-found errors for canonical callers.
        from cac.core import boss, encounter
        from cac.core import campaign as campaign_core

        error = {
            "boss": boss.BossNotFoundError,
            "campaign": campaign_core.CampaignNotFoundError,
            "encounter": encounter.EncounterNotFoundError,
        }[domain]
        suffix = f" in campaign {campaign!r}" if domain == "encounter" else ""
        raise error(f"{domain.capitalize()} {value!r} does not exist{suffix}.")

    def campaign(self, value: str | None, *, mutable: bool = False) -> str:
        from cac.core import campaign

        if value is None:
            # Active state already supplies an exact canonical identity.
            return campaign.resolve_campaign(self.root, None, require_mutable=mutable)
        canonical = self.resolve("campaign", value)
        return campaign.resolve_campaign(self.root, canonical, require_mutable=mutable)

    def encounter(
        self, value: str, campaign: str | None, *, mutable: bool = False, missing_literal: bool = False
    ) -> tuple[str, str]:
        if "/" in value:
            parts = value.split("/")
            if (
                len(parts) != 2
                or not config.SHORT_REFERENCE_PATTERN.fullmatch(parts[0])
                or not config.SHORT_REFERENCE_PATTERN.fullmatch(parts[1])
            ):
                raise ReferenceError(f"Invalid qualified encounter reference {value!r}; expected cNNN/eNNN.")
            qualified_campaign = self.resolve("campaign", parts[0])
            if campaign is not None and self.campaign(campaign) != qualified_campaign:
                raise ReferenceError("Qualified encounter reference conflicts with the explicit campaign.")
            campaign, value = qualified_campaign, parts[1]
        self.validate(value)
        selected = self.campaign(campaign, mutable=mutable)
        return selected, self.resolve("encounter", value, selected, missing_literal=missing_literal)

    def identity(self, domain: str, canonical: str, campaign: str | None = None) -> dict[str, Any]:
        prefix = {"boss": "b", "campaign": "c", "encounter": "e"}[domain]
        match = config.NUMBERED_NAME_PATTERN.fullmatch(canonical) or config.SHORT_REFERENCE_PATTERN.fullmatch(canonical)
        result = {"canonical": canonical, "short": None, "reason": "unnumbered"}
        if campaign is not None:
            result["campaign"] = campaign
        if not match or match[1] != prefix or int(match[2]) == 0:
            return result
        bare = f"{prefix}{int(match[2]):03d}"
        try:
            if self.resolve(domain, bare, campaign) != canonical:
                raise AmbiguousReferenceError("The numeric reference selects a different record.")
            if domain == "encounter":
                parent = self.identity("campaign", campaign)
                if parent["short"] is None:
                    return {**result, "reason": "campaign_" + parent["reason"]}
                result["short"] = f"{parent['short']}/{bare}"
                result["bare_short"] = bare
            else:
                result["short"] = bare
            result["reason"] = None
        except AmbiguousReferenceError:
            result["reason"] = "ambiguous"
        except FileNotFoundError:
            result["reason"] = "missing"
        except (ValueError, OSError):
            result["reason"] = "invalid_storage"
        return result


@dataclass(frozen=True)
class Selection:
    name: str | None
    campaign: str | None
    dependency: str | None


def select(
    root: Path,
    domain: str,
    name: str | None = None,
    *,
    campaign: str | None = None,
    dependency: str | None = None,
    create: bool = False,
    mutable: bool = False,
    remove: bool = False,
    inventory: Inventory | None = None,
) -> Selection:
    """Public core input boundary; domain/storage routines below it consume exact names."""
    inventory = inventory or Inventory(root)
    if domain == "encounter":
        if create or name is None:
            campaign = inventory.campaign(campaign, mutable=mutable)
        else:
            campaign, name = inventory.encounter(name, campaign, mutable=mutable)
        if dependency is not None:
            selected, dependency = inventory.encounter(dependency, campaign, missing_literal=remove)
            if selected != campaign:
                raise ReferenceError("Encounter prerequisites must belong to the source campaign.")
    else:
        if name is not None and not create:
            name = inventory.resolve(domain, name)
        if dependency is not None:
            dependency = inventory.resolve(domain, dependency, missing_literal=remove)
    return Selection(name, campaign, dependency)


def inputs(
    domain: str, *, create: bool = False, mutable: bool = False, remove: bool = False, reporter: Callable | None = None
):
    """Thin Python entry adapter shared by CLI and MCP; selection rules live in select."""

    def decorate(function):
        parameters = signature(function)

        @wraps(function)
        def invoke(*args, **kwargs):
            bound = parameters.bind(*args, **kwargs)
            bound.apply_defaults()
            values = bound.arguments
            root = resolve_project_root()
            inventory = Inventory(root)
            target_key = "encounter" if "encounter" in values else "name"
            selection = select(
                root,
                domain,
                values.get(target_key),
                campaign=values.get("campaign"),
                dependency=values.get("dependency"),
                create=create,
                mutable=mutable,
                remove=remove,
                inventory=inventory,
            )
            if target_key in values:
                values[target_key] = selection.name
            if "campaign" in values:
                values["campaign"] = selection.campaign
            if "dependency" in values:
                values["dependency"] = selection.dependency
            identity = None
            if selection.name is not None and not create:
                identity = inventory.identity(domain, selection.name, selection.campaign)
            result = function(*bound.args, **bound.kwargs)
            if selection.name is not None:
                if identity is None:
                    identity = Inventory(root).identity(domain, selection.name, selection.campaign)
                if "delete" in function.__name__.split("_"):
                    identity = {key: value for key, value in identity.items() if key != "bare_short"}
                    identity.update(short=None, reason="deleted")
                if isinstance(result, dict):
                    result = {**result, "identity": identity}
                    if domain == "campaign" and isinstance(result.get("body"), str):
                        from cac.core import campaign as campaign_core

                        result = campaign_core.budget_response(root, selection.name, result)
                    elif isinstance(result.get("body"), str):
                        allowance = max(0, config.RESPONSE_BUDGET - len(encoded(identity)) - 14)
                        if len(result["body"]) > allowance:
                            from cac.core import boss, encounter
                            from cac.core import campaign as campaign_core

                            path = (
                                boss.boss_path(root, selection.name)
                                if domain == "boss"
                                else campaign_core.campaign_path(root, selection.name)
                                if domain == "campaign"
                                else encounter.encounter_path(root, selection.campaign, selection.name)
                            )
                            result["body"] = budget.truncate_body(result["body"], path, budget=allowance)
                if reporter is not None:
                    reporter(identity)
            return result

        invoke.reference_contract = {"domain": domain, "create": create, "mutable": mutable, "remove": remove}
        syntax = "bNNN" if domain == "boss" else "cNNN" if domain == "campaign" else "eNNN or cNNN/eNNN"
        invoke.__doc__ = (function.__doc__ or "") + (
            f"\nExisting {domain} targets accept full canonical names or {syntax}; refs include archived records and reject ambiguity. "
            "Create names are literal. Qualified encounter context overrides active fallback and must agree with an explicit campaign. "
            "Resolved identity metadata retains canonical names; numbering and Git automation are not performed."
        )
        return invoke

    return decorate


def identity_page(root: Path, domain: str, items: list, cursor: str | None, *, campaign: str | None = None) -> dict:
    """Budget original items and parallel additive identities as one compact JSON page."""
    inventory = Inventory(root)
    entries = [
        (item, inventory.identity(domain, item if isinstance(item, str) else item["name"], campaign)) for item in items
    ]
    base = {"items": [], "identities": [], "next_cursor": str(len(items)) if items else None}
    available = config.RESPONSE_BUDGET - len(encoded(base)) - 2
    if available < 0:
        raise ReferenceError("Reference page envelope exceeds the response budget.")
    for item, identity in entries:
        if len(encoded(item)) + len(encoded(identity)) + 2 > available:
            raise ReferenceError(
                "Canonical identity exceeds the response budget; increase it or inspect a single record."
            )
    page = budget.paginate(
        entries, cursor, budget=available, render=lambda pair: encoded(pair[0]) + encoded(pair[1]) + ","
    )
    return {
        "items": [entry[0] for entry in page.items],
        "identities": [entry[1] for entry in page.items],
        "next_cursor": page.next_cursor,
    }


def identity_order(root: Path, items: list[dict], campaign: str) -> list[dict]:
    inventory = Inventory(root)
    result = [{**item, "identity": inventory.identity("encounter", item["name"], campaign)} for item in items]
    if len(encoded(result)) > config.RESPONSE_BUDGET:
        raise ReferenceError(
            "Encounter order including identities exceeds the response budget; inspect paged encounter_list instead."
        )
    return result


def body_allowance(root: Path, domain: str, canonical: str, campaign: str | None = None) -> int:
    """Reserve identity metadata before truncating CLI body output."""
    return max(0, config.RESPONSE_BUDGET - len(encoded(Inventory(root).identity(domain, canonical, campaign))) - 14)
