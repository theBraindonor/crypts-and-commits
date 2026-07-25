from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar

from cac.core import config

T = TypeVar("T")


class InvalidCursorError(ValueError):
    """Raised when a supplied pagination cursor is not a valid page marker."""


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    next_cursor: str | None


def truncate_body(content: str, file_path: Path, budget: int | None = None) -> str:
    """Return `content` unchanged if it fits within `budget` characters (default
    `config.RESPONSE_BUDGET`, read at call time so it can be overridden per-call or patched in
    tests). Otherwise prepend a truncation notice naming `file_path` as a direct-read fallback,
    and cut the body to leave room for that notice within the same budget."""
    budget = config.RESPONSE_BUDGET if budget is None else budget
    if len(content) <= budget:
        return content
    notice = _notice(file_path, budget)
    available = max(budget - len(notice), 0)
    return f"{notice}{content[:available]}"


def _notice(file_path: Path, budget: int) -> str:
    return (
        f"[TRUNCATED: this content exceeds the {budget:,}-character response budget and has been "
        f"cut short below. Read the full content directly from disk at: {file_path}]\n\n"
    )


def paginate(
    items: Sequence[T],
    cursor: str | None,
    *,
    render: Callable[[T], str] = str,
    budget: int | None = None,
) -> Page[T]:
    """Page `items` under `budget` characters (default `config.RESPONSE_BUDGET`, measured via
    `render`), resuming after `cursor` (an opaque offset token taken from a prior page's
    `next_cursor`). Always includes at least one item per page - even one whose rendered form
    alone exceeds budget - so paging cannot stall."""
    budget = config.RESPONSE_BUDGET if budget is None else budget
    start = _parse_cursor(cursor, len(items))
    selected: list[T] = []
    used = 0
    for index in range(start, len(items)):
        item = items[index]
        cost = len(render(item)) + 1
        if selected and used + cost > budget:
            return Page(items=selected, next_cursor=str(index))
        selected.append(item)
        used += cost
    return Page(items=selected, next_cursor=None)


def _parse_cursor(cursor: str | None, length: int) -> int:
    if cursor is None:
        return 0
    try:
        index = int(cursor)
    except ValueError as exc:
        raise InvalidCursorError(f"Cursor {cursor!r} is not valid.") from exc
    if index < 0 or index > length:
        raise InvalidCursorError(f"Cursor {cursor!r} is out of range.")
    return index
