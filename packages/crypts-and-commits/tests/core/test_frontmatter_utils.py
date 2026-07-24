import frontmatter

from cac.core.frontmatter_utils import append_log_entry, toggle_list_attribute


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


def test_append_log_entry_creates_section_on_first_call() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    append_log_entry(post, section="Log", heading="Review", message="Looks good.")

    assert post.content == "Body.\n\n## Log\n\n### Review\n\nLooks good.\n"


def test_append_log_entry_appends_under_existing_section() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    append_log_entry(post, section="Log", heading="Review", message="Looks good.")
    append_log_entry(post, section="Log", heading="Opened", message="Go ahead.")

    assert post.content.count("## Log") == 1
    assert "### Review" in post.content
    assert "### Opened" in post.content
    assert post.content.index("### Review") < post.content.index("### Opened")


def test_append_log_entry_strips_message_whitespace() -> None:
    post = frontmatter.loads("---\nname: test\n---\n\nBody.")

    append_log_entry(post, section="Log", heading="Review", message="  Looks good.  \n")

    assert post.content == "Body.\n\n## Log\n\n### Review\n\nLooks good.\n"
