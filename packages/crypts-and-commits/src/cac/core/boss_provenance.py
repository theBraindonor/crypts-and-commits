"""Validated, immutable snapshots of roadmap context supplied during adoption."""

import re
from datetime import UTC, date, datetime

PROGRESS = ("planned", "in_progress", "completed")
_FIELDS = {"kind", "progress", "source", "message", "completed_on"}


def validate(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ValueError("Boss provenance must contain kind, progress, source, message, and completed_on.")
    if value["kind"] != "roadmap" or value["progress"] not in PROGRESS:
        raise ValueError("Boss provenance requires kind=roadmap and progress=planned, in_progress, or completed.")
    for key in ("source", "message"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f"Boss provenance {key} must be nonblank text.")
    completed = value["completed_on"]
    if completed is not None:
        if value["progress"] != "completed":
            raise ValueError("completed_on is permitted only for completed roadmap progress.")
        if not isinstance(completed, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", completed):
            raise ValueError("completed_on must be an ISO YYYY-MM-DD date or null.")
        try:
            parsed = date.fromisoformat(completed)
        except ValueError as exc:
            raise ValueError("completed_on must be a valid calendar date.") from exc
        if parsed > datetime.now(UTC).date():
            raise ValueError("completed_on cannot be a future date (UTC).")
    return value.copy()


def external_completion(metadata: dict) -> bool:
    value = metadata.get("provenance")
    return value is not None and validate(value)["progress"] == "completed"
