from pathlib import Path

import pytest
from cac.core import budget


def test_truncate_body_passes_through_when_under_budget() -> None:
    content = "short body"

    assert budget.truncate_body(content, Path("lore/example.md"), budget=100) == content


def test_truncate_body_passes_through_when_exactly_at_budget() -> None:
    content = "x" * 100

    assert budget.truncate_body(content, Path("lore/example.md"), budget=100) == content


def test_truncate_body_prepends_notice_naming_path_when_over_budget() -> None:
    content = "x" * 500
    path = Path("lore/example.md")

    result = budget.truncate_body(content, path, budget=100)

    assert result.startswith("[TRUNCATED")
    assert str(path) in result
    assert "100" in result


def test_truncate_body_truncates_content_to_fit_remaining_budget() -> None:
    content = "abcdefghij" * 200
    path = Path("lore/example.md")

    result = budget.truncate_body(content, path, budget=1000)

    assert result != content
    assert content[:10] in result
    assert len(result) <= 1000


def test_truncate_body_over_budget_notice_alone_exceeds_tiny_budget() -> None:
    # When the notice itself is longer than the budget, no content survives, but the notice
    # is still returned in full rather than being cut off mid-sentence.
    content = "x" * 1000
    path = Path("lore/example.md")

    result = budget.truncate_body(content, path, budget=5)

    assert result.startswith("[TRUNCATED")
    assert not result.endswith("x")


def test_truncate_body_uses_config_response_budget_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 10)

    result = budget.truncate_body("x" * 100, Path("lore/example.md"))

    assert result.startswith("[TRUNCATED")


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
