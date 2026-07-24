import re
from pathlib import Path

import frontmatter


def write_post(path: Path, post: frontmatter.Post) -> None:
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")


def toggle_list_attribute(
    post: frontmatter.Post, key: str, *, add: str | None = None, remove: str | None = None
) -> None:
    values = set(post.get(key, []) or [])
    if add is not None:
        values.add(add)
    if remove is not None:
        values.discard(remove)
    post[key] = sorted(values)


def append_log_entry(post: frontmatter.Post, *, section: str, heading: str, message: str) -> None:
    """Append a '### <heading>' entry under a running '## <section>' section at the end of
    `post.content`, creating the section on first use."""
    body = post.content.rstrip()
    entry = f"### {heading}\n\n{message.strip()}"
    section_pattern = re.compile(rf"(?m)^## {re.escape(section)}\s*$")
    if section_pattern.search(body):
        post.content = f"{body}\n\n{entry}\n"
    else:
        block = f"## {section}\n\n{entry}"
        post.content = f"{body}\n\n{block}\n" if body else f"{block}\n"
