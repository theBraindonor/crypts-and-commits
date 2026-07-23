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
