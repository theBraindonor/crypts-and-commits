"""Content evidence for the derived index; never infer freshness from file times."""

import hashlib
import sqlite3
from pathlib import Path

import frontmatter

from cac.core import config
from cac.core.paths import sourcebook_dir

VERSION = "1"
TABLE = "source_snapshot"
META = "source_snapshot_format"
COLUMNS = "object_type,campaign,name,location,digest"


def supported(connection: sqlite3.Connection) -> bool:
    try:
        return connection.execute(f"SELECT version FROM {META}").fetchall() == [(VERSION,)]
    except sqlite3.Error:
        return False


def record(root: Path, path: Path) -> tuple:
    from cac.core import boss, search_index

    boss._safe_path(root, path)
    content = path.read_bytes()
    # Parsing matters even when the file's hash happens to match a prior snapshot.
    frontmatter.loads(content.decode("utf-8"))
    return (
        *search_index._classify(root, path)[:3],
        path.relative_to(sourcebook_dir(root)).as_posix(),
        hashlib.sha256(content).hexdigest(),
    )


def inventory(root: Path) -> list[tuple]:
    from cac.core import boss

    base = sourcebook_dir(root)

    def children(directory: Path) -> list[Path]:
        boss._safe_path(root, directory / "_probe.md")
        # iterdir propagates access failures; glob can silently suppress them.
        return sorted(directory.iterdir()) if directory.exists() else []

    world = base / config.WORLD_FILE_NAME
    paths = [world] if world.exists() or world.is_symlink() else []
    for directory in (
        config.LORE_DIR_NAME,
        config.REGION_DIR_NAME,
        config.CAMPAIGN_DIR_NAME,
        config.BOSS_DIR_NAME,
        f"{config.ARCHIVE_DIR_NAME}/{config.CAMPAIGN_DIR_NAME}",
        f"{config.ARCHIVE_DIR_NAME}/{config.BOSS_DIR_NAME}",
    ):
        paths.extend(path for path in children(base / directory) if path.suffix == ".md")
    for directory in (base / config.ENCOUNTER_DIR_NAME, base / config.ARCHIVE_DIR_NAME / config.ENCOUNTER_DIR_NAME):
        for parent in children(directory):
            if parent.is_dir() or parent.is_symlink():
                paths.extend(path for path in children(parent) if path.suffix == ".md")
    records = [record(root, path) for path in paths]
    keys = [entry[:3] for entry in records]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate live/archive source identities.")
    return sorted(records)


def initialize(connection: sqlite3.Connection, records: list[tuple]) -> None:
    connection.execute(f"DROP TABLE IF EXISTS {TABLE}")
    connection.execute(f"DROP TABLE IF EXISTS {META}")
    connection.execute(f"CREATE TABLE {META} (version TEXT NOT NULL)")
    connection.execute(f"INSERT INTO {META} VALUES (?)", (VERSION,))
    connection.execute(
        f"CREATE TABLE {TABLE} (object_type TEXT,campaign TEXT,name TEXT,location TEXT,digest TEXT,"
        "PRIMARY KEY(object_type,campaign,name))"
    )
    connection.executemany(f"INSERT INTO {TABLE} VALUES (?,?,?,?,?)", records)


def sync(connection: sqlite3.Connection, root: Path, path: Path, *, delete: bool = False) -> None:
    from cac.core import search_index

    if not supported(connection):
        return  # Incremental writes cannot upgrade or bless a legacy cache.
    key = search_index._classify(root, path)[:3]
    connection.execute(f"DELETE FROM {TABLE} WHERE object_type=? AND campaign=? AND name=?", key)
    if not delete:
        connection.execute(f"INSERT INTO {TABLE} VALUES (?,?,?,?,?)", record(root, path))


def check(connection: sqlite3.Connection, root: Path) -> None:
    if not supported(connection):
        raise ValueError("Missing or unsupported index snapshot format.")
    expected = sorted(connection.execute(f"SELECT {COLUMNS} FROM {TABLE}").fetchall())
    if inventory(root) != expected:
        raise ValueError("Source contents or record locations differ from the indexed snapshot.")


def capture(connection: sqlite3.Connection, keys: list[tuple]) -> list[tuple] | None:
    if not supported(connection):
        return None
    return [
        row
        for key in keys
        for row in connection.execute(
            f"SELECT {COLUMNS} FROM {TABLE} WHERE object_type=? AND campaign=? AND name=?", key
        ).fetchall()
    ]


def restore(connection: sqlite3.Connection, keys: list[tuple], records: list[tuple] | None) -> None:
    if records is None:
        return
    if not supported(connection):
        raise ValueError("Index snapshot format disappeared during recovery.")
    for key in keys:
        connection.execute(f"DELETE FROM {TABLE} WHERE object_type=? AND campaign=? AND name=?", key)
    connection.executemany(f"INSERT INTO {TABLE} VALUES (?,?,?,?,?)", records)
