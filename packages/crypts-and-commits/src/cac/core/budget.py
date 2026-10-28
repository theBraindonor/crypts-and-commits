import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from cac.core import config

T = TypeVar("T")


class InvalidCursorError(ValueError):
    """Raised when a supplied pagination cursor is not a valid page marker."""


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    next_cursor: str | None


def _encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def body_page(
    body: str,
    cursor: str | None,
    build: Callable[[str, str | None], dict],
    *,
    label: str = "Body",
    budget: int | None = None,
    measure: Callable[[dict], int] | None = None,
) -> dict:
    """Return the largest page of `body` that fits `budget`, starting at `cursor`.

    `build(text, next_cursor)` renders one page. By default a page is measured as compact JSON,
    so metadata and escaping count against the budget; `measure` overrides that. Cursors are
    bound to the body's content hash, so a cursor from before an edit fails instead of splicing
    two versions together."""
    budget = config.RESPONSE_BUDGET if budget is None else budget
    size = measure or (lambda page: len(_encoded(page)))
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    start = 0
    if cursor is not None:
        try:
            version, offset = cursor.split(":")
            start = int(offset)
        except (ValueError, AttributeError) as exc:
            raise InvalidCursorError(f"Invalid {label.lower()} body cursor.") from exc
        if version != digest or start < 0 or start > len(body):
            raise InvalidCursorError(f"{label} cursor is stale or out of range; restart get without a cursor.")

    def page(end: int) -> dict:
        return build(body[start:end], f"{digest}:{end}" if end < len(body) else None)

    if size(page(len(body))) <= budget:
        return page(len(body))
    if size(page(start)) > budget:
        raise ValueError(f"{label} response metadata exceeds the response budget; increase it.")
    low, high = start, len(body) - 1
    while low < high:
        middle = (low + high + 1) // 2
        if size(page(middle)) <= budget:
            low = middle
        else:
            high = middle - 1
    if low == start:
        raise ValueError(f"{label} response budget cannot fit a body character; increase it.")
    return page(low)


def fit_response(
    result: dict,
    cursor: str | None,
    continuation: str,
    *,
    budget: int | None = None,
    measure: Callable[[dict], int] | None = None,
) -> dict:
    """Fit a get-style result (with a string `body`) to the budget. A truncated page gains
    `next_cursor` and a `notice` naming the continuation call; a complete page keeps its shape.
    Bodies are never prefixed, so pages reassemble exactly."""
    body = result["body"]

    def build(text: str, next_cursor: str | None) -> dict:
        page = {**result, "body": text}
        if next_cursor is not None:
            page["next_cursor"] = next_cursor
            page["notice"] = (
                f"[TRUNCATED: body continues. Call {continuation} for this record with cursor=next_cursor "
                "(CLI: --cursor) for the next page.]"
            )
        return page

    return body_page(body, cursor, build, budget=budget, measure=measure)


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
