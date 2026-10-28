"""Canonical campaign membership, including read-only legacy scalar support."""

from typing import Any

from cac.core import config


class MembershipError(ValueError):
    """Invalid campaign boss membership or conflicting storage representations."""


def order(name: str) -> tuple:
    match = config.NUMBERED_NAME_PATTERN.fullmatch(name) or config.SHORT_REFERENCE_PATTERN.fullmatch(name)
    return (0, int(match[2]), name) if match and match[1] == "b" else (1, 0, name)


def validate(names: Any) -> list[str]:
    from cac.core import boss

    if not isinstance(names, list):
        raise MembershipError("Campaign bosses must be a list of canonical boss names.")
    for name in names:
        boss.validate_name(name)
    if len(set(names)) != len(names):
        raise ValueError("Duplicate campaign boss identities.")
    return sorted(names, key=order)


def read(metadata: dict) -> list[str]:
    if "boss" in metadata and "bosses" in metadata:
        raise ValueError("Campaign has both boss and bosses fields; reconcile the conflicting representations.")
    if "bosses" in metadata:
        return validate(metadata["bosses"])
    scalar = metadata.get("boss")
    return validate([] if scalar is None else [scalar])


def store(metadata: dict, names: list[str]) -> None:
    metadata.pop("boss", None)
    metadata["bosses"] = validate(names)


def resolve(root, names: list[str]) -> list[str]:
    from cac.core import references

    validate(names)
    inventory = references.Inventory(root)
    return validate([inventory.resolve("boss", name) for name in names])
