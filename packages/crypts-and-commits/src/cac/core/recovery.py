"""Scoped exception recovery for managed records and their existing logical index rows.

This is not a crash journal or a cross-process transaction/claim service.
"""

import sqlite3
from collections import Counter
from pathlib import Path

from cac.core import config, index_snapshot, search_index
from cac.core.paths import search_index_db_path

_COLUMNS = "object_type,campaign,name,status,updated_on,archived,body"


class RecoveryError(RuntimeError):
    """Rollback failed; the message identifies records requiring explicit recovery."""


class Recovery:
    def __init__(self, root: Path, paths: list[Path]):
        self.root = root
        self.files = {path: path.read_bytes() if path.exists() else None for path in dict.fromkeys(paths)}
        self.index = search_index_db_path(root)
        self.keys = sorted({classified[:3] for path in paths if (classified := search_index._classify(root, path))})
        self.rows = []
        self.snapshot = None
        if self.index.exists():
            with sqlite3.connect(self.index) as connection:
                self.snapshot = index_snapshot.capture(connection, self.keys)
                for key in self.keys:
                    self.rows.extend(
                        connection.execute(
                            f"SELECT {_COLUMNS} FROM {config.SEARCH_INDEX_FTS_TABLE} WHERE object_type=? AND campaign=? AND name=?",
                            key,
                        ).fetchall()
                    )

    def __enter__(self):
        return self

    def _restore_index(self):
        if not self.index.exists():
            if self.rows or self.snapshot is not None:
                raise RecoveryError(f"Existing index disappeared: {self.index}")
            return
        with sqlite3.connect(self.index) as connection:
            index_snapshot.restore(connection, self.keys, self.snapshot)
            current = []
            for key in self.keys:
                current.extend(
                    connection.execute(
                        f"SELECT {_COLUMNS} FROM {config.SEARCH_INDEX_FTS_TABLE} WHERE object_type=? AND campaign=? AND name=?",
                        key,
                    ).fetchall()
                )
            if Counter(current) == Counter(self.rows):
                return
            for key in self.keys:
                connection.execute(
                    f"DELETE FROM {config.SEARCH_INDEX_FTS_TABLE} WHERE object_type=? AND campaign=? AND name=?", key
                )
            connection.executemany(
                f"INSERT INTO {config.SEARCH_INDEX_FTS_TABLE} ({_COLUMNS}) VALUES (?,?,?,?,?,?,?)", self.rows
            )

    def __exit__(self, error_type, error, traceback):
        if error is None:
            return False
        failed = []
        for path, original in self.files.items():
            try:
                if original is None:
                    if path.exists():
                        path.unlink()
                elif not path.exists() or path.read_bytes() != original:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(original)
            except (OSError, ValueError) as failure:
                failed.append(f"{path} (expected {'original bytes' if original is not None else 'absent'}): {failure}")
        try:
            self._restore_index()
        except (sqlite3.Error, RecoveryError, OSError, ValueError) as failure:
            failed.append(f"index rows {self.keys}: {failure}")
        if failed:
            raise RecoveryError(
                f"Operation failed ({error}); recovery incomplete. Inspect: {'; '.join(failed)}"
            ) from error
        return False
