import re
from datetime import UTC, datetime

import frontmatter
import pytest
from cac.core import frontmatter_utils
from cac.core.config import SUMMARY_MAX_LENGTH
from cac.core.frontmatter_utils import (
    SUMMARY_ABSENT_MESSAGE,
    SummaryTooLongError,
    append_log_entry,
    set_summary_attribute,
    summary_or_placeholder,
    toggle_list_attribute,
)


def test_toggle_list_attribute_adds_value() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    toggle_list_attribute(post, "items", add="alpha")

    assert post["items"] == ["alpha"]


def test_toggle_list_attribute_is_idempotent_on_add() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    toggle_list_attribute(post, "items", add="alpha")
    toggle_list_attribute(post, "items", add="alpha")

    assert post["items"] == ["alpha"]


def test_toggle_list_attribute_removes_value() -> None:
    post = frontmatter.loads("---\nname: test\nitems:\n  - alpha\n  - beta\n---\n\nBody.")

    toggle_list_attribute(post, "items", remove="alpha")

    assert post["items"] == ["beta"]


def test_toggle_list_attribute_remove_missing_value_is_noop() -> None:
    post = frontmatter.loads("---\nname: test\nitems:\n  - beta\n---\n\nBody.")

    toggle_list_attribute(post, "items", remove="alpha")

    assert post["items"] == ["beta"]


def test_toggle_list_attribute_sorts_result() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    toggle_list_attribute(post, "items", add="zeta")
    toggle_list_attribute(post, "items", add="alpha")

    assert post["items"] == ["alpha", "zeta"]


def test_set_summary_attribute_stores_value() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    set_summary_attribute(post, "A brief routing signal.")

    assert post["summary"] == "A brief routing signal."


def test_set_summary_attribute_accepts_value_at_cap() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    set_summary_attribute(post, "x" * SUMMARY_MAX_LENGTH)

    assert post["summary"] == "x" * SUMMARY_MAX_LENGTH


def test_set_summary_attribute_rejects_value_over_cap() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    with pytest.raises(SummaryTooLongError):
        set_summary_attribute(post, "x" * (SUMMARY_MAX_LENGTH + 1))


def test_summary_or_placeholder_returns_stored_value() -> None:
    post = frontmatter.loads("---\nname: test\nsummary: Stored summary.\n---\n\nBody.")

    assert summary_or_placeholder(post) == "Stored summary."


def test_summary_or_placeholder_returns_message_when_absent() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    assert summary_or_placeholder(post) == SUMMARY_ABSENT_MESSAGE


def test_summary_or_placeholder_returns_message_when_empty() -> None:
    post = frontmatter.loads('---\nname: test\nsummary: ""\n---\n\nBody.')

    assert summary_or_placeholder(post) == SUMMARY_ABSENT_MESSAGE


_FIXED_TIME = datetime(2026, 7, 23, 18, 4, 12, tzinfo=UTC)


def _freeze_time(monkeypatch: pytest.MonkeyPatch, when: datetime = _FIXED_TIME) -> None:
    monkeypatch.setattr(frontmatter_utils, "utcnow", lambda: when)


def test_append_log_entry_creates_section_on_first_call(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_time(monkeypatch)
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    append_log_entry(post, section="Log", heading="Review", message="Looks good.", user="John Hoff")

    assert post.content == "Body.\n\n## Log\n\n### Review - 2026-07-23T18:04:12Z - John Hoff\n\nLooks good.\n"


def test_append_log_entry_appends_under_existing_section(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_time(monkeypatch)
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    append_log_entry(post, section="Log", heading="Review", message="Looks good.", user="John Hoff")
    append_log_entry(post, section="Log", heading="Opened", message="Go ahead.", user="John Hoff")

    assert post.content.count("## Log") == 1
    assert "### Review" in post.content
    assert "### Opened" in post.content
    assert post.content.index("### Review") < post.content.index("### Opened")


def test_append_log_entry_strips_message_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_time(monkeypatch)
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    append_log_entry(post, section="Log", heading="Review", message="  Looks good.  \n", user="John Hoff")

    assert post.content == "Body.\n\n## Log\n\n### Review - 2026-07-23T18:04:12Z - John Hoff\n\nLooks good.\n"


def test_append_log_entry_includes_user() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    append_log_entry(post, section="Log", heading="Review", message="Looks good.", user="Jane Doe")

    assert "- Jane Doe" in post.content


def test_append_log_entry_uses_real_utc_timestamp_by_default() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    append_log_entry(post, section="Log", heading="Review", message="Looks good.", user="John Hoff")

    match = re.search(r"### Review - (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) - John Hoff", post.content)
    assert match is not None
    parsed = datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    assert abs((datetime.now(UTC) - parsed).total_seconds()) < 60
