"""Freeform campaign discoveries, independent of campaign lifecycle locks."""

import hashlib
from pathlib import Path
from typing import Any

from cac.core import boss, budget, config, references, world
from cac.core.paths import sourcebook_dir


def _directory(root: Path) -> Path:
    return sourcebook_dir(root) / config.BOSS_DIR_NAME / config.RUMORS_DIR_NAME


def _path(root: Path, canonical: str) -> Path:
    references.Inventory.validate(canonical)
    return boss._safe_path(root, _directory(root) / f"{canonical}.md")


def _owner(root: Path, campaign: str | None) -> tuple[str, dict[str, Any]]:
    world.read_world(root)
    inventory = references.Inventory(root)
    inventory.names("campaign")
    canonical = inventory.campaign(campaign)
    # Active fallback must undergo the same safe inventory validation as explicit refs.
    inventory.resolve("campaign", canonical)
    return canonical, inventory.identity("campaign", canonical)


def read_body(root: Path, campaign: str | None = None) -> str:
    canonical, _ = _owner(root, campaign)
    path = _path(root, canonical)
    if not path.exists():
        raise ValueError(f"Rumors for campaign {canonical!r} do not exist.")
    return path.read_bytes().decode("utf-8")


def _bounded(result: dict[str, Any]) -> dict[str, Any]:
    if len(references.encoded(result)) > config.RESPONSE_BUDGET:
        raise ValueError("Rumors response identifiers exceed the response budget; increase it.")
    return result


def get(root: Path, campaign: str | None = None, cursor: str | None = None) -> dict[str, Any]:
    canonical, identity = _owner(root, campaign)
    body = read_body(root, canonical)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    start = 0
    if cursor is not None:
        try:
            version, offset = cursor.split(":")
            start = int(offset)
        except (ValueError, AttributeError) as exc:
            raise budget.InvalidCursorError("Invalid rumors body cursor.") from exc
        if version != digest or start < 0 or start > len(body):
            raise budget.InvalidCursorError("Rumors cursor is stale or out of range; restart get without a cursor.")

    def response(end: int) -> dict[str, Any]:
        more = end < len(body)
        return {
            "campaign": canonical,
            "identity": identity,
            "body": body[start:end],
            "truncated": more,
            "next_cursor": f"{digest}:{end}" if more else None,
            "notice": "TRUNCATED: continue rumors get with next_cursor and the same campaign." if more else None,
        }

    result = response(len(body))
    if len(references.encoded(result)) <= config.RESPONSE_BUDGET:
        return result
    # Budget the serialized envelope too, including JSON escaping and continuation metadata.
    low, high = start, len(body) - 1
    _bounded(response(start))
    while low < high:
        middle = (low + high + 1) // 2
        if len(references.encoded(response(middle))) <= config.RESPONSE_BUDGET:
            low = middle
        else:
            high = middle - 1
    if low == start:
        raise ValueError("Rumors response budget cannot fit a body character; increase it.")
    return _bounded(response(low))


def write(root: Path, body: str, campaign: str | None = None, *, update: bool = False) -> dict[str, Any]:
    canonical, identity = _owner(root, campaign)
    path = _path(root, canonical)
    if path.exists() != update:
        state = "do not exist" if update else "already exist"
        raise ValueError(f"Rumors for campaign {canonical!r} {state}.")
    content = body.encode("utf-8")
    result = _bounded({"campaign": canonical, "identity": identity})
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents an accidental overwrite by create.
    with path.open("wb" if update else "xb") as target:
        target.write(content)
    return result


def delete(root: Path, campaign: str | None = None) -> dict[str, Any]:
    canonical, identity = _owner(root, campaign)
    path = _path(root, canonical)
    result = _bounded({"campaign": canonical, "identity": identity})
    if not path.exists():
        raise ValueError(f"Rumors for campaign {canonical!r} do not exist.")
    path.unlink()
    return result


def list_documents(root: Path, cursor: str | None = None) -> dict[str, Any]:
    world.read_world(root)
    directory = _directory(root)
    boss._safe_path(root, directory / "_probe.md")
    inventory = references.Inventory(root)
    owners = set(inventory.names("campaign"))
    items = []
    for path in sorted(directory.glob("*.md")):
        _path(root, path.stem)
        orphaned = path.stem not in owners
        items.append(
            {
                "campaign": path.stem,
                "identity": None if orphaned else inventory.identity("campaign", path.stem),
                "diagnostic": "Campaign owner is missing; reconcile retained history." if orphaned else None,
            }
        )
    # Use the shared cursor validation and ordering contract, then bound the whole envelope.
    page = budget.paginate(items, cursor, render=references.encoded)
    selected = list(page.items)
    start = int(cursor or "0")
    while True:
        end = start + len(selected)
        result = {"items": selected, "next_cursor": str(end) if end < len(items) else None}
        if len(references.encoded(result)) <= config.RESPONSE_BUDGET:
            return result
        if len(selected) <= 1:
            return _bounded(result)
        selected.pop()
