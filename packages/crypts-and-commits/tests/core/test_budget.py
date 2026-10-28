import pytest
from cac.core import budget


def test_fit_response_passes_through_at_exact_budget() -> None:
    result = {"body": "x" * 400}
    size = len('{"body":""}') + 400
    assert budget.fit_response(result, None, "lore_get", budget=size) == result
    assert budget.fit_response(result, None, "lore_get", budget=size - 1)["next_cursor"]


def test_fit_response_uses_config_response_budget_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 400)
    page = budget.fit_response({"body": "x" * 1000}, None, "lore_get")
    assert page["next_cursor"] and len(page["body"]) < 400


def test_paginate_returns_single_page_when_under_budget() -> None:
    items = ["alpha", "beta", "gamma"]

    page = budget.paginate(items, None, budget=1000)

    assert page.items == items
    assert page.next_cursor is None


def test_paginate_pages_multiple_items_under_budget() -> None:
    items = ["aa", "bb", "cc", "dd", "dd"]

    first = budget.paginate(items, None, budget=6)

    assert first.items == ["aa", "bb"]
    assert first.next_cursor == "2"


def test_paginate_resumes_from_cursor() -> None:
    items = ["aa", "bb", "cc", "dd", "ee"]

    first = budget.paginate(items, None, budget=6)
    second = budget.paginate(items, first.next_cursor, budget=6)
    third = budget.paginate(items, second.next_cursor, budget=6)

    assert first.items == ["aa", "bb"]
    assert second.items == ["cc", "dd"]
    assert third.items == ["ee"]
    assert third.next_cursor is None


def test_paginate_always_includes_at_least_one_item_even_if_over_budget() -> None:
    items = ["a-very-long-single-item", "next"]

    page = budget.paginate(items, None, budget=5)

    assert page.items == ["a-very-long-single-item"]
    assert page.next_cursor == "1"


def test_paginate_accepts_custom_render_function() -> None:
    items = [("alpha", "open"), ("beta", "draft")]

    page = budget.paginate(items, None, render=lambda entry: f"{entry[0]} ({entry[1]})", budget=1000)

    assert page.items == items
    assert page.next_cursor is None


def test_paginate_uses_config_response_budget_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 6)
    items = ["aa", "bb", "cc"]

    page = budget.paginate(items, None)

    assert page.items == ["aa", "bb"]
    assert page.next_cursor == "2"


def test_paginate_rejects_non_numeric_cursor() -> None:
    with pytest.raises(budget.InvalidCursorError):
        budget.paginate(["a", "b"], "not-a-number")


def test_paginate_rejects_negative_cursor() -> None:
    with pytest.raises(budget.InvalidCursorError):
        budget.paginate(["a", "b"], "-1")


def test_paginate_rejects_out_of_range_cursor() -> None:
    with pytest.raises(budget.InvalidCursorError):
        budget.paginate(["a", "b"], "5")


def test_paginate_accepts_cursor_at_exact_length_returning_empty_page() -> None:
    page = budget.paginate(["a", "b"], "2")

    assert page.items == []
    assert page.next_cursor is None


def test_paginate_empty_items_returns_empty_page() -> None:
    page = budget.paginate([], None)

    assert page.items == []
    assert page.next_cursor is None


BODY = 'Intro "quoted" \\ back\nCafé ✓ — [tool.ruff] ' * 120


def _render(text: str, next_cursor: str | None) -> dict:
    return {"metadata": {"name": "x"}, "body": text, "next_cursor": next_cursor}


def _encoded(value: object) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def test_body_page_reassembles_exact_body_within_serialized_budget() -> None:
    pages, cursor = [], None
    while True:
        page = budget.body_page(BODY, cursor, _render, budget=700)
        assert len(_encoded(page)) <= 700
        pages.append(page["body"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert len(pages) > 2 and "".join(pages) == BODY


@pytest.mark.parametrize("cursor", ["bad", "x:1", "a:b:c", None])
def test_body_page_rejects_invalid_and_stale_cursors(cursor: str | None) -> None:
    first = budget.body_page(BODY, None, _render, budget=700)
    if cursor is None:
        cursor = first["next_cursor"]
        body = BODY + "edited"
    else:
        body = BODY
    with pytest.raises(budget.InvalidCursorError):
        budget.body_page(body, cursor, _render, budget=700)


def test_body_page_rejects_out_of_range_offset() -> None:
    digest = budget.body_page(BODY, None, _render, budget=700)["next_cursor"].split(":")[0]
    with pytest.raises(budget.InvalidCursorError):
        budget.body_page(BODY, f"{digest}:{len(BODY) + 1}", _render, budget=700)


def test_body_page_fails_explicitly_when_metadata_cannot_fit() -> None:
    with pytest.raises(ValueError, match="response budget"):
        budget.body_page(BODY, None, lambda text, cursor: {"metadata": "m" * 800, "body": text}, budget=700)


def test_fit_response_keeps_complete_shape_and_marks_truncation() -> None:
    small = {"metadata": {"a": 1}, "body": "short"}
    assert budget.fit_response(small, None, "lore_get") == small
    page = budget.fit_response({"metadata": {"a": 1}, "body": BODY}, None, "lore_get", budget=700)
    assert page["next_cursor"] and "lore_get" in page["notice"] and BODY.startswith(page["body"])
    assert ".sourcebook" not in page["notice"]
