"""Freeform campaign discoveries, independent of campaign lifecycle locks."""

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

    def response(text: str, next_cursor: str | None) -> dict[str, Any]:
        return {
            "campaign": canonical,
            "identity": identity,
            "body": text,
            "truncated": next_cursor is not None,
            "next_cursor": next_cursor,
            "notice": "TRUNCATED: continue rumors get with next_cursor and the same campaign." if next_cursor else None,
        }

    return budget.body_page(body, cursor, response, label="Rumors")


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
