import re
from datetime import UTC, datetime
from pathlib import Path

import frontmatter

from cac.core import git_utils, search_index
from cac.core.config import (
    CREATED_BY_KEY,
    CREATED_ON_KEY,
    SUMMARY_KEY,
    SUMMARY_MAX_LENGTH,
    UPDATED_BY_KEY,
    UPDATED_ON_KEY,
)

SUMMARY_ABSENT_MESSAGE = "No summary has been set for this entry; read the full body instead."


class SummaryTooLongError(ValueError):
    """Raised when a summary exceeds the maximum allowed length."""


def set_summary_attribute(post: frontmatter.Post, summary: str) -> None:
    """Set the summary field on a post, rejecting a value over the length cap."""
    if len(summary) > SUMMARY_MAX_LENGTH:
        raise SummaryTooLongError(
            f"Summary is {len(summary)} characters, which exceeds the maximum of {SUMMARY_MAX_LENGTH}. "
            "Shorten it to a brief routing signal - it is not a substitute for the body."
        )
    post[SUMMARY_KEY] = summary


def summary_or_placeholder(post: frontmatter.Post) -> str:
    """Return the stored summary, or an explicit placeholder message when none is set."""
    value = post.get(SUMMARY_KEY)
    if not value:
        return SUMMARY_ABSENT_MESSAGE
    return value


def utcnow() -> datetime:
    return datetime.now(UTC)


def format_timestamp(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def write_post(root: Path, path: Path, post: frontmatter.Post) -> None:
    path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
    search_index.sync_write(root, path, post)


def delete_post(root: Path, path: Path) -> Path:
    path.unlink()
    search_index.sync_delete(root, path)
    return path


def stamp_created(post: frontmatter.Post, root: Path) -> str:
    user = git_utils.current_git_user(root)
    ts = format_timestamp(utcnow())
    post[CREATED_BY_KEY] = user
    post[CREATED_ON_KEY] = ts
    post[UPDATED_BY_KEY] = user
    post[UPDATED_ON_KEY] = ts
    return user


def stamp_updated(post: frontmatter.Post, root: Path) -> str:
    user = git_utils.current_git_user(root)
    post[UPDATED_BY_KEY] = user
    post[UPDATED_ON_KEY] = format_timestamp(utcnow())
    return user


def toggle_list_attribute(
    post: frontmatter.Post, key: str, *, add: str | None = None, remove: str | None = None
) -> None:
    values = set(post.get(key, []) or [])
    if add is not None:
        values.add(add)
    if remove is not None:
        values.discard(remove)
    post[key] = sorted(values)


def append_log_entry(post: frontmatter.Post, *, section: str, heading: str, message: str, user: str) -> None:
    """Append a '### <heading>' entry under a running '## <section>' section at the end of
    `post.content`, creating the section on first use."""
    body = post.content.rstrip()
    ts = format_timestamp(utcnow())
    entry = f"### {heading} - {ts} - {user}\n\n{message.strip()}"
    section_pattern = re.compile(rf"(?m)^## {re.escape(section)}\s*$")
    if section_pattern.search(body):
        post.content = f"{body}\n\n{entry}\n"
    else:
        block = f"## {section}\n\n{entry}"
        post.content = f"{body}\n\n{block}\n" if body else f"{block}\n"
