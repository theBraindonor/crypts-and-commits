import sqlite3
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from cac.core.config import (
    CAMPAIGN_DIR_NAME,
    ENCOUNTER_DIR_NAME,
    LORE_DIR_NAME,
    REGION_DIR_NAME,
    SEARCH_DEFAULT_MAX_RESULTS,
    SEARCH_DEFAULT_SNIPPET_TOKENS,
    SEARCH_INDEX_BUSY_TIMEOUT_MS,
    SEARCH_INDEX_FTS_TABLE,
    SEARCH_INDEX_OBJECT_TYPE_CAMPAIGN,
    SEARCH_INDEX_OBJECT_TYPE_ENCOUNTER,
    SEARCH_INDEX_OBJECT_TYPE_LORE,
    SEARCH_INDEX_OBJECT_TYPE_REGION,
    SEARCH_INDEX_OBJECT_TYPE_WORLD,
    SEARCH_INDEX_OBJECT_TYPES,
    SEARCH_MAX_SNIPPET_TOKENS,
    SEARCH_MIN_SNIPPET_TOKENS,
    WORLD_FILE_NAME,
)
from cac.core.paths import search_index_db_path, sourcebook_dir

_CREATE_TABLE_SQL = (
    f"CREATE VIRTUAL TABLE IF NOT EXISTS {SEARCH_INDEX_FTS_TABLE} USING fts5("
    "object_type UNINDEXED, campaign UNINDEXED, name UNINDEXED, status UNINDEXED, updated_on UNINDEXED, body, "
    "tokenize='porter unicode61')"
)
_BODY_COLUMN_INDEX = 5


class EmptySearchPhraseError(ValueError):
    pass


class InvalidSearchQueryError(ValueError):
    pass


@dataclass(frozen=True)
class SearchHit:
    rank: int
    score: float
    object_type: str
    campaign: str
    name: str
    status: str
    updated_on: str
    excerpt: str


def _connect(root: Path) -> sqlite3.Connection:
    """Open a fresh connection, creating the `.index` directory and schema if needed. Callers own
    the connection's full lifecycle - commit and close it within the same function that opened it;
    never cache or hold it open across calls, so other processes always see committed writes."""
    path = search_index_db_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA busy_timeout = {SEARCH_INDEX_BUSY_TIMEOUT_MS}")
    conn.execute(_CREATE_TABLE_SQL)
    conn.commit()
    return conn


def rebuild_index(root: Path) -> int:
    """Fully rebuild the index from `.sourcebook` content on disk - a drop-and-reindex, not a
    merge. Returns the total number of items indexed."""
    conn = _connect(root)
    try:
        conn.execute(f"DROP TABLE IF EXISTS {SEARCH_INDEX_FTS_TABLE}")
        conn.execute(_CREATE_TABLE_SQL)
        count = (
            _reindex_encounters(root, conn)
            + _reindex_world(root, conn)
            + _reindex_lore(root, conn)
            + _reindex_regions(root, conn)
            + _reindex_campaigns(root, conn)
        )
        conn.commit()
        return count
    finally:
        conn.close()


def _reindex_encounters(root: Path, conn: sqlite3.Connection) -> int:
    from cac.core import campaign as campaign_core
    from cac.core import encounter as encounter_core

    count = 0
    for campaign in campaign_core.list_campaigns(root):
        for name in encounter_core.list_encounters(root, campaign):
            metadata, body = encounter_core.read_metadata(root, campaign, name)
            conn.execute(
                f"INSERT INTO {SEARCH_INDEX_FTS_TABLE} "
                "(object_type, campaign, name, status, updated_on, body) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    SEARCH_INDEX_OBJECT_TYPE_ENCOUNTER,
                    campaign,
                    name,
                    metadata.get("status", ""),
                    metadata.get("updated_on", ""),
                    body,
                ),
            )
            count += 1
    return count


def _reindex_world(root: Path, conn: sqlite3.Connection) -> int:
    from cac.core import world as world_core

    try:
        world = world_core.read_world(root)
    except world_core.WorldNotFoundError:
        return 0
    conn.execute(
        f"INSERT INTO {SEARCH_INDEX_FTS_TABLE} "
        "(object_type, campaign, name, status, updated_on, body) VALUES (?, ?, ?, ?, ?, ?)",
        (
            SEARCH_INDEX_OBJECT_TYPE_WORLD,
            "",
            world.metadata.get("name") or SEARCH_INDEX_OBJECT_TYPE_WORLD,
            "",
            world.metadata.get("updated_on", ""),
            world.body,
        ),
    )
    return 1


def _reindex_lore(root: Path, conn: sqlite3.Connection) -> int:
    from cac.core import lore as lore_core

    count = 0
    for name in lore_core.list_lore(root):
        metadata, body = lore_core.read_metadata(root, name)
        status = "enabled" if metadata.get("enabled", True) else "disabled"
        conn.execute(
            f"INSERT INTO {SEARCH_INDEX_FTS_TABLE} "
            "(object_type, campaign, name, status, updated_on, body) VALUES (?, ?, ?, ?, ?, ?)",
            (
                SEARCH_INDEX_OBJECT_TYPE_LORE,
                "",
                name,
                status,
                metadata.get("updated_on", ""),
                body,
            ),
        )
        count += 1
    return count


def _reindex_regions(root: Path, conn: sqlite3.Connection) -> int:
    from cac.core import region as region_core

    count = 0
    for name in region_core.list_regions(root):
        metadata, body = region_core.read_metadata(root, name)
        conn.execute(
            f"INSERT INTO {SEARCH_INDEX_FTS_TABLE} "
            "(object_type, campaign, name, status, updated_on, body) VALUES (?, ?, ?, ?, ?, ?)",
            (
                SEARCH_INDEX_OBJECT_TYPE_REGION,
                "",
                name,
                "",
                metadata.get("updated_on", ""),
                body,
            ),
        )
        count += 1
    return count


def _reindex_campaigns(root: Path, conn: sqlite3.Connection) -> int:
    from cac.core import campaign as campaign_core

    count = 0
    for name in campaign_core.list_campaigns(root):
        metadata, body = campaign_core.read_metadata(root, name)
        conn.execute(
            f"INSERT INTO {SEARCH_INDEX_FTS_TABLE} "
            "(object_type, campaign, name, status, updated_on, body) VALUES (?, ?, ?, ?, ?, ?)",
            (
                SEARCH_INDEX_OBJECT_TYPE_CAMPAIGN,
                "",
                name,
                metadata.get("status", ""),
                metadata.get("updated_on", ""),
                body,
            ),
        )
        count += 1
    return count


def _classify(root: Path, path: Path) -> tuple[str, str, str] | None:
    """Map a `.sourcebook` file path to `(object_type, campaign, name)` for incremental sync,
    where `name` is the filename stem (`campaign` is `""` for non-encounter types). Returns
    `None` for anything unrecognized."""
    try:
        rel = path.relative_to(sourcebook_dir(root))
    except ValueError:
        return None
    if rel == Path(WORLD_FILE_NAME):
        return SEARCH_INDEX_OBJECT_TYPE_WORLD, "", path.stem
    parts = rel.parts
    if len(parts) == 2 and parts[0] == LORE_DIR_NAME:
        return SEARCH_INDEX_OBJECT_TYPE_LORE, "", path.stem
    if len(parts) == 2 and parts[0] == REGION_DIR_NAME:
        return SEARCH_INDEX_OBJECT_TYPE_REGION, "", path.stem
    if len(parts) == 2 and parts[0] == CAMPAIGN_DIR_NAME:
        return SEARCH_INDEX_OBJECT_TYPE_CAMPAIGN, "", path.stem
    if len(parts) == 3 and parts[0] == ENCOUNTER_DIR_NAME:
        return SEARCH_INDEX_OBJECT_TYPE_ENCOUNTER, parts[1], path.stem
    return None  # anything unrecognized


def sync_write(root: Path, path: Path, post: frontmatter.Post) -> None:
    """Incrementally patch the index for a single create/update, as one short transaction.
    No-op if the index has never been built (see `rebuild_index`) - incremental sync must
    never bring an index into existence on its own - or if `path` isn't an indexed object
    type."""
    if not search_index_db_path(root).exists():
        return
    classified = _classify(root, path)
    if classified is None:
        return
    object_type, campaign, stem = classified

    if object_type == SEARCH_INDEX_OBJECT_TYPE_WORLD:
        name = post.get("name") or SEARCH_INDEX_OBJECT_TYPE_WORLD
        status = ""
    elif object_type == SEARCH_INDEX_OBJECT_TYPE_LORE:
        name = stem
        status = "enabled" if post.get("enabled", True) else "disabled"
    else:
        name = stem
        status = post.get("status", "")

    conn = _connect(root)
    try:
        conn.execute(
            f"DELETE FROM {SEARCH_INDEX_FTS_TABLE} WHERE object_type = ? AND campaign = ? AND name = ?",
            (object_type, campaign, name),
        )
        conn.execute(
            f"INSERT INTO {SEARCH_INDEX_FTS_TABLE} "
            "(object_type, campaign, name, status, updated_on, body) VALUES (?, ?, ?, ?, ?, ?)",
            (object_type, campaign, name, status, post.get("updated_on", ""), post.content),
        )
        conn.commit()
    finally:
        conn.close()


def sync_delete(root: Path, path: Path) -> None:
    """Incrementally remove a single deleted object's row from the index, as one short
    transaction. No-op if the index has never been built or `path` isn't an indexed type."""
    if not search_index_db_path(root).exists():
        return
    classified = _classify(root, path)
    if classified is None:
        return
    object_type, campaign, name = classified

    conn = _connect(root)
    try:
        conn.execute(
            f"DELETE FROM {SEARCH_INDEX_FTS_TABLE} WHERE object_type = ? AND campaign = ? AND name = ?",
            (object_type, campaign, name),
        )
        conn.commit()
    finally:
        conn.close()


def index_counts(root: Path) -> dict[str, int] | None:
    """Return the number of indexed items per `object_type`, or `None` if the index has never
    been built. Does not create the index file - a status check is read-only."""
    path = search_index_db_path(root)
    if not path.exists():
        return None
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            f"SELECT object_type, COUNT(*) FROM {SEARCH_INDEX_FTS_TABLE} GROUP BY object_type"
        ).fetchall()
        return dict(rows)
    finally:
        conn.close()


def _phrase_literal(phrase: str) -> str:
    """Wrap `phrase` as a single FTS5 phrase-query literal, so the whole input is matched
    literally and in order - any FTS5 operators embedded in it (`-`, `OR`, `*`, `"`, ...) are
    neutralized rather than interpreted as query syntax."""
    return '"' + phrase.replace('"', '""') + '"'


def search(
    root: Path,
    phrase: str,
    *,
    object_type: str | None = None,
    limit: int = SEARCH_DEFAULT_MAX_RESULTS,
    offset: int = 0,
    snippet_tokens: int = SEARCH_DEFAULT_SNIPPET_TOKENS,
) -> list[SearchHit] | None:
    """Search indexed content for `phrase`, ranked by relevance. Returns `None` if the index has
    never been built (a search is a read and must not create the index file), or the matching
    page of `SearchHit`s otherwise - possibly empty if nothing matched."""
    if not phrase.strip():
        raise EmptySearchPhraseError("Search phrase must not be empty.")
    if limit < 1:
        raise InvalidSearchQueryError(f"max_results must be at least 1, got {limit}.")
    if offset < 0:
        raise InvalidSearchQueryError(f"skip must be at least 0, got {offset}.")
    if object_type is not None and object_type not in SEARCH_INDEX_OBJECT_TYPES:
        valid = ", ".join(SEARCH_INDEX_OBJECT_TYPES)
        raise InvalidSearchQueryError(f"Unknown document type {object_type!r}; valid types are: {valid}.")
    if not (SEARCH_MIN_SNIPPET_TOKENS <= snippet_tokens <= SEARCH_MAX_SNIPPET_TOKENS):
        raise InvalidSearchQueryError(
            f"snippet_tokens must be between {SEARCH_MIN_SNIPPET_TOKENS} and {SEARCH_MAX_SNIPPET_TOKENS}, "
            f"got {snippet_tokens}."
        )

    path = search_index_db_path(root)
    if not path.exists():
        return None

    conn = sqlite3.connect(path)
    try:
        sql = (
            "SELECT object_type, campaign, name, status, updated_on, "
            f"snippet({SEARCH_INDEX_FTS_TABLE}, {_BODY_COLUMN_INDEX}, '**', '**', '...', {snippet_tokens}), "
            f"bm25({SEARCH_INDEX_FTS_TABLE}) "
            f"FROM {SEARCH_INDEX_FTS_TABLE} WHERE {SEARCH_INDEX_FTS_TABLE} MATCH ?"
        )
        params: list[object] = [_phrase_literal(phrase)]
        if object_type is not None:
            sql += " AND object_type = ?"
            params.append(object_type)
        sql += f" ORDER BY bm25({SEARCH_INDEX_FTS_TABLE}) LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(sql, params).fetchall()
        return [
            SearchHit(
                rank=offset + position,
                score=row[6],
                object_type=row[0],
                campaign=row[1],
                name=row[2],
                status=row[3],
                updated_on=row[4],
                excerpt=row[5],
            )
            for position, row in enumerate(rows, start=1)
        ]
    finally:
        conn.close()
