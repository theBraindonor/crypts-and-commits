"""Canonical boss/campaign ownership, promotion, and guarded lifecycle coupling."""

from functools import wraps
from pathlib import Path

import frontmatter
import yaml

from cac.core import boss, campaign_bosses, config, frontmatter_utils, references, search_index, templates
from cac.core.recovery import Recovery


class LinkError(ValueError):
    """Missing, inconsistent, or competing current ownership. No automatic repair."""


class CampaignLinkedError(LinkError):
    """An origin or reverse current claim protects campaign history from deletion."""


def preflight_campaign_creation(root: Path, name: str) -> None:
    """Prevent ordinary create from reusing retained identities or orphan current claims."""
    from cac.core import campaign

    campaign.validate_name(name)
    for directory in (campaign.campaign_dir(root), campaign.archive_campaign_dir(root)):
        path = boss._safe_path(root, directory / f"{name}.md")
        if path.exists():
            raise campaign.CampaignAlreadyExistsError(f"Campaign {name!r} already exists, live or archived.")
    for key in references.Inventory(root).names("boss"):
        _, post = boss._load(root, key)
        if post.get("campaign") == name:
            raise LinkError(
                f"Campaign name {name!r} is already claimed by boss {key!r}; inspect the missing reciprocal record."
            )


def _campaign(root: Path, name: str) -> tuple[Path, frontmatter.Post]:
    from cac.core import campaign

    campaign.validate_name(name)
    live = boss._safe_path(root, campaign.campaign_dir(root) / f"{name}.md")
    archived = boss._safe_path(root, campaign.archive_campaign_dir(root) / f"{name}.md")
    if live.exists() and archived.exists():
        raise LinkError(f"Campaign {name!r} exists live and archived.")
    path = live if live.exists() else archived
    if not path.exists():
        raise campaign.CampaignNotFoundError(f"Campaign {name!r} does not exist.")
    try:
        post = frontmatter.load(path)
    except yaml.YAMLError as error:
        raise LinkError(f"Campaign {name!r} has invalid frontmatter: {error}") from error
    if (
        post.get("name", name) != name
        or post.get("status", "draft") not in config.CAMPAIGN_STATUSES
        or type(post.get("archived", False)) is not bool
        or post.get("archived", False) != (path == archived)
    ):
        raise LinkError(f"Campaign {name!r} has invalid name/status/archive metadata.")
    try:
        campaign_bosses.read(post.metadata)
    except (ValueError, TypeError) as error:
        raise LinkError(f"Campaign {name!r} has invalid boss membership: {error}") from error
    return path, post


class Links:
    def __init__(self, root: Path):
        self.root = root
        self.inventory = references.Inventory(root)
        try:
            self.bosses = {name: boss._load(root, name) for name in self.inventory.names("boss")}
            self.campaigns = {name: _campaign(root, name) for name in self.inventory.names("campaign")}
        except (ValueError, OSError, TypeError, yaml.YAMLError) as error:
            raise LinkError(f"Cannot validate canonical boss/campaign ownership: {error}") from error

    def claims(self, name: str) -> list[str]:
        return [key for key, (_, post) in self.bosses.items() if post.get("campaign") == name]

    def current(self, name: str) -> list[str]:
        """Validate current or explicitly released historical ownership for a campaign."""
        _, post = self.campaigns[name]
        origins, claims = campaign_bosses.read(post.metadata), self.claims(name)
        for origin in origins:
            if origin not in self.bosses:
                raise LinkError(f"Campaign {name!r} references missing origin boss {origin!r}.")
        if post.get("status", "draft") == "abandoned":
            if claims:
                raise LinkError(f"Abandoned campaign {name!r} still has current boss claims {claims}.")
            # A released origin may now be owned elsewhere; validate without changing it.
            for origin in origins:
                other = self.bosses[origin][1].get("campaign")
                if other is not None:
                    self._pair(origin, other)
            return []
        if set(claims) != set(origins):
            raise LinkError(f"Campaign {name!r} has inconsistent reciprocal boss membership/claims.")
        for origin in origins:
            self._pair(origin, name)
        return origins

    def _pair(self, origin: str, name: str) -> None:
        if name not in self.campaigns:
            raise LinkError(f"Boss {origin!r} references missing campaign {name!r}.")
        _, goal = self.bosses[origin]
        _, post = self.campaigns[name]
        origins = campaign_bosses.read(post.metadata)
        if goal.get("campaign") != name or origin not in origins or set(self.claims(name)) != set(origins):
            raise LinkError(f"Boss {origin!r} and campaign {name!r} have inconsistent reciprocal ownership.")
        competitors = [
            key
            for key, (_, other) in self.campaigns.items()
            if origin in campaign_bosses.read(other.metadata) and other.get("status", "draft") != "abandoned"
        ]
        if competitors != [name]:
            raise LinkError(f"Boss {origin!r} has competing campaign claims: {competitors}.")
        expected = {"available": ("draft", "open", "paused"), "vanquished": ("completed",)}
        if post.get("status", "draft") not in expected.get(goal["status"], ()) or goal.get(
            "archived", False
        ) != post.get("archived", False):
            raise LinkError(f"Boss {origin!r} and campaign {name!r} have inconsistent lifecycle/archive state.")


def inspection(root: Path, name: str) -> dict:
    try:
        links = Links(root)
        current = links.current(name)
        origin = campaign_bosses.read(links.campaigns[name][1].metadata)
        return {"kind": "current" if current else "historical" if origin else "bossless", "diagnostics": []}
    except (ValueError, OSError, TypeError, KeyError, yaml.YAMLError) as error:
        text = str(error)
        return {
            "kind": "invalid",
            "diagnostics": [text[:800]],
            "truncated": len(text) > 800,
            "refs": ["boss_list", "campaign_list"],
        }


def _body_suffix(original: bytes) -> tuple[bytes, bytes]:
    lines = original.splitlines(keepends=True)
    if not lines or lines[0].strip() != b"---":
        raise LinkError("Boss record has no supported frontmatter header; body cannot be preserved safely.")
    offset = len(lines[0])
    for line in lines[1:]:
        offset += len(line)
        if line.strip() == b"---":
            ending = b"\r\n" if line.endswith(b"\r\n") else b"\n" if line.endswith(b"\n") else b""
            return ending, original[offset:]
    raise LinkError("Boss frontmatter is not terminated.")


def _write_boss(root: Path, destination: Path, post: frontmatter.Post, original: bytes) -> None:
    ending, suffix = _body_suffix(original)
    header = frontmatter.dumps(frontmatter.Post("", **post.metadata)).encode("utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(header + ending + suffix)
    search_index.sync_write(root, destination, post)


def _bounded_pair(result: dict) -> dict:
    if len(references.encoded({**result, "identity": result["boss_identity"]})) > config.RESPONSE_BUDGET:
        raise LinkError("Assignment identities exceed the response budget before any write.")
    return result


def _pair_result(root: Path, name: str, campaign_name: str, status: str, *, reused: bool) -> dict:
    inventory = references.Inventory(root)
    return _bounded_pair(
        {
            "boss": name,
            "campaign": campaign_name,
            "status": status,
            "reused": reused,
            "boss_identity": inventory.identity("boss", name),
            "campaign_identity": inventory.identity("campaign", campaign_name),
        }
    )


def assign_campaign(root: Path, name: str, campaign_name: str, body: str) -> dict:
    from cac.core import campaign

    campaign.validate_name(campaign_name)
    links = Links(root)
    _, goal = boss._load(root, name)
    if goal.get("campaign") is not None:
        if campaign_name not in links.campaigns:
            raise LinkError(f"Boss {name!r} is assigned to a missing or different campaign.")
        if goal["campaign"] != campaign_name or name not in links.current(campaign_name):
            raise LinkError(f"Boss {name!r} is already assigned or has inconsistent ownership.")
        return _pair_result(root, name, campaign_name, links.campaigns[campaign_name][1]["status"], reused=True)
    if campaign_name in links.campaigns or links.claims(campaign_name):
        raise LinkError(f"Campaign name {campaign_name!r} is retained or already claimed.")
    destination = boss._safe_path(root, campaign.campaign_dir(root) / f"{campaign_name}.md")
    archived = boss._safe_path(root, campaign.archive_campaign_dir(root) / f"{campaign_name}.md")
    if destination.exists() or archived.exists():
        raise LinkError(f"Campaign name {campaign_name!r} already exists.")
    # Compute complete output before persistence, including hypothetical new canonical identity.
    inventory = references.Inventory(root)
    inventory.names("campaign")
    inventory.cache["campaign", None].append(campaign_name)
    match = config.NUMBERED_NAME_PATTERN.fullmatch(campaign_name) or config.SHORT_REFERENCE_PATTERN.fullmatch(
        campaign_name
    )
    if match:
        inventory.numeric["campaign", None].setdefault((match[1], int(match[2])), []).append(campaign_name)
    result = {
        "boss": name,
        "campaign": campaign_name,
        "status": "draft",
        "reused": False,
        "boss_identity": inventory.identity("boss", name),
        "campaign_identity": inventory.identity("campaign", campaign_name),
    }
    # The entry adapter adds the boss identity too; reserve it in preflight.
    _bounded_pair(result)
    create_group(root, campaign_name, body, [name])
    return result


def _minimum_output(root: Path, name: str, post: frontmatter.Post, **extras) -> None:
    names = campaign_bosses.read(post.metadata)
    # Reserve both campaign-read representations plus adapter identity overhead.
    required = {
        **extras,
        "name": name,
        "bosses": names,
        "metadata": post.metadata,
        "body": "",
        "identity": {"canonical": name, "short": None, "reason": "ambiguous"},
        "status": post.get("status", "draft"),
        "archived": post.get("archived", False),
        "boss_link": {"kind": "current", "diagnostics": []},
    }
    if len(references.encoded(required)) + 300 > config.RESPONSE_BUDGET:
        raise LinkError("Campaign membership/state exceeds the response budget before writes; increase it.")


def _eligible(root: Path, names: list[str], links: Links) -> None:
    from cac.core import boss_candidates

    for name in names:
        _, goal = links.bosses[name]
        boss._editable(goal, name, ("available",))
        evaluation = boss_candidates.assess(root, name)
        if not evaluation["eligible"]:
            blocked = [entry["name"] for entry in evaluation["prerequisites"] if not entry["satisfied"]]
            raise LinkError(
                f"Boss {name!r} is not eligible: {evaluation['reason_codes']}; "
                f"unsatisfied prerequisites {blocked[:8]}. Inspect boss_candidates/boss_get."
            )


def create_group(root: Path, name: str, body: str, names: list[str]) -> Path:
    from cac.core import campaign

    names = campaign_bosses.resolve(root, names)
    preflight_campaign_creation(root, name)
    links = Links(root)
    _eligible(root, names, links)
    destination = boss._safe_path(root, campaign.campaign_dir(root) / f"{name}.md")
    post = frontmatter.loads(templates.load("sourcebook", "campaign.md"))
    post["name"], post.content = name, body
    campaign_bosses.store(post.metadata, names)
    frontmatter_utils.stamp_created(post, root)
    changes = []
    for member in names:
        path, goal = links.bosses[member]
        original = path.read_bytes()
        _body_suffix(original)
        goal["campaign"] = name
        frontmatter_utils.stamp_updated(goal, root)
        changes.append((path, goal, original))
    _minimum_output(root, name, post)
    with Recovery(root, [destination] + [path for path, _, _ in changes]):
        destination.parent.mkdir(parents=True, exist_ok=True)
        frontmatter_utils.write_post(root, destination, post)
        for path, goal, original in changes:
            _write_boss(root, path, goal, original)
    return destination


def set_bosses(root: Path, name: str, names: list[str], message: str) -> Path:
    from cac.core import campaign

    names = campaign_bosses.resolve(root, names)
    path, post = _campaign(root, name)
    if post.get("status", "draft") != "draft" or post.get("archived", False):
        raise campaign.CampaignNotMutableError("Boss membership can change only on an unarchived draft campaign.")
    if not message or not message.strip():
        raise campaign.CampaignMessageRequiredError("A nonblank message is required for boss membership changes.")
    links = Links(root)
    previous = links.current(name)
    if names == previous:
        return path
    _eligible(root, [member for member in names if member not in previous], links)
    changes = []
    for member in sorted(set(names) ^ set(previous), key=campaign_bosses.order):
        target, goal = links.bosses[member]
        original = target.read_bytes()
        _body_suffix(original)
        if member in names:
            goal["campaign"] = name
        else:
            goal.metadata.pop("campaign", None)
        frontmatter_utils.stamp_updated(goal, root)
        changes.append((target, goal, original))
    campaign_bosses.store(post.metadata, names)
    user = frontmatter_utils.stamp_updated(post, root)
    frontmatter_utils.append_log_entry(
        post,
        section="Log",
        heading="Bosses changed",
        message=f"{message.strip()}\n\nPrevious bosses: {previous}\nNew bosses: {names}",
        user=user,
    )
    _minimum_output(root, name, post)
    with Recovery(root, [path] + [target for target, _, _ in changes]):
        frontmatter_utils.write_post(root, path, post)
        for target, goal, original in changes:
            _write_boss(root, target, goal, original)
    return path


def _archive_paths(root: Path, name: str, path: Path, post: frontmatter.Post, goal_paths: list[Path]) -> list[Path]:
    from cac.core import campaign, encounter

    if post.get("archived", False):
        raise campaign.CampaignAlreadyArchivedError(f"Campaign {name!r} is already archived.")
    paths = [path, campaign.archive_campaign_dir(root) / path.name]
    for key in encounter.list_encounters(root, name):
        source = encounter.encounter_dir(root, name) / f"{key}.md"
        paths.extend([source, encounter.archive_encounter_dir(root, name) / source.name])
    for goal_path in goal_paths:
        paths.extend([goal_path, boss.boss_dir(root, archived=True) / goal_path.name])
    for index, candidate in enumerate(paths):
        boss._safe_path(root, candidate)
        if index % 2 and candidate.exists():
            raise LinkError(f"Archive destination collision at {candidate}.")
    return paths


def campaign_operation(action: str):
    """Guard existing domain operations and recover their whole affected cohort."""

    def decorate(function):
        @wraps(function)
        def invoke(root: Path, name: str, *args, **kwargs):
            from cac.core import campaign

            # Preserve ordinary missing-record error behavior before enumerating claims.
            path, post = _campaign(root, name)
            links = Links(root)
            if action == "delete" and (campaign_bosses.read(post.metadata) or links.claims(name)):
                raise CampaignLinkedError(
                    f"Cannot delete campaign {name!r}: origin/reverse boss links protect its history."
                )
            current = links.current(name)
            if post.get("archived", False) and action not in ("archive", "delete"):
                raise campaign.CampaignNotMutableError(f"Campaign {name!r} is archived and cannot be changed.")
            goals = [links.bosses[member] for member in current]
            paths = [path] + [target for target, _ in goals]
            if action == "archive":
                paths = _archive_paths(root, name, path, post, [target for target, _ in goals])
            changes = []
            for goal_path, goal in goals:
                original = goal_path.read_bytes()
                _body_suffix(original)
                if action in ("complete", "abandon", "reactivate", "archive"):
                    goal["status"] = (
                        "vanquished"
                        if action == "complete"
                        else "available"
                        if action in ("abandon", "reactivate")
                        else goal["status"]
                    )
                    if action == "abandon":
                        goal.metadata.pop("campaign", None)
                    destination = goal_path
                    if action == "archive":
                        goal["archived"] = True
                        destination = boss.boss_dir(root, archived=True) / goal_path.name
                    frontmatter_utils.stamp_updated(goal, root)
                    changes.append((goal_path, destination, goal, original))
            preview = frontmatter.Post(post.content, **post.metadata)
            frontmatter_utils.stamp_updated(preview, root)
            if action == "archive":
                from cac.core import encounter

                _minimum_output(root, name, preview, archived_encounters=encounter.list_encounters(root, name))
            else:
                _minimum_output(root, name, preview)
            with Recovery(root, paths):
                result = function(root, name, *args, **kwargs)
                for goal_path, destination, goal, original in changes:
                    _write_boss(root, destination, goal, original)
                    if destination != goal_path:
                        goal_path.unlink()
                return result

        return invoke

    return decorate


def boss_diagnostics(root: Path, records: dict) -> dict[str, list[dict]]:
    """Expose campaign-side orphan/competing claims to the unbounded eligibility evaluator."""
    from cac.core import campaign

    result: dict[str, list[dict]] = {}
    for directory in (campaign.campaign_dir(root), campaign.archive_campaign_dir(root)):
        boss._safe_path(root, directory / "_probe.md")
    names = sorted(set(campaign.list_campaigns(root) + campaign.list_archived_campaigns(root)))
    for name in names:
        try:
            _, post = _campaign(root, name)
        except (ValueError, OSError, yaml.YAMLError) as error:
            issue = {"name": name, "code": "invalid_campaign_origin", "campaign": name, "message": str(error)}
            result.setdefault("campaign:" + name, []).append(issue)
            # Route diagnostics to every plausible claim without choosing a representation.
            try:
                raw = frontmatter.load(campaign.campaign_path(root, name)).metadata
                claims = [raw.get("boss")] + (raw.get("bosses") if isinstance(raw.get("bosses"), list) else [])
                for member in claims:
                    if isinstance(member, str) and member in records:
                        result.setdefault(member, []).append(issue)
            except (ValueError, OSError, yaml.YAMLError):
                pass  # The campaign-level diagnostic above remains authoritative.
            continue
        declared = campaign_bosses.read(post.metadata)
        claims = [member for member, goal in records.items() if goal.get("campaign") == name]
        if post.get("status", "draft") != "abandoned" and set(declared) != set(claims):
            for member in set(declared) | set(claims):
                result.setdefault(member, []).append(
                    {
                        "name": member,
                        "code": "campaign_boss_mismatch",
                        "campaign": name,
                        "message": "Campaign membership does not match all current boss claims.",
                    }
                )
        for origin in campaign_bosses.read(post.metadata):
            goal = records.get(origin)
            historical = post.get("status", "draft") == "abandoned"
            if (
                goal is None
                or (not historical and goal.get("campaign") != name)
                or (historical and goal.get("campaign") == name)
            ):
                result.setdefault(origin, []).append(
                    {
                        "name": origin,
                        "code": "orphan_campaign_claim",
                        "campaign": name,
                        "message": "Campaign origin/current ownership disagree; abandoned origins must be released.",
                    }
                )
    return result
