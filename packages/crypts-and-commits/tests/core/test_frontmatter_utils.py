import frontmatter

from cac.core.frontmatter_utils import toggle_list_attribute


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
