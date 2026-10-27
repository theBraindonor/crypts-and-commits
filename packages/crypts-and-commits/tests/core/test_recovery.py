import sqlite3

import frontmatter
import pytest
from cac.core import campaign, config, frontmatter_utils, search_index, world
from cac.core.paths import search_index_db_path
from cac.core.recovery import Recovery, RecoveryError


def index_bodies(root):
    with sqlite3.connect(search_index_db_path(root)) as connection:
        return dict(
            connection.execute(
                f"SELECT name,body FROM {config.SEARCH_INDEX_FTS_TABLE} WHERE object_type='campaign'"
            ).fetchall()
        )


def test_recovery_is_scoped_to_affected_files_and_rows(tmp_path):
    world.initialize_world(tmp_path)
    affected = campaign.create_campaign(tmp_path, "affected", "Before")
    unrelated = campaign.create_campaign(tmp_path, "unrelated", "Before")
    search_index.rebuild_index(tmp_path)
    before = affected.read_bytes()
    with pytest.raises(OSError), Recovery(tmp_path, [affected]):
        post = frontmatter.load(affected)
        post.content = "Failed change"
        frontmatter_utils.write_post(tmp_path, affected, post)
        other = frontmatter.load(unrelated)
        other.content = "Independent change"
        frontmatter_utils.write_post(tmp_path, unrelated, other)
        raise OSError("Operation failed")
    assert affected.read_bytes() == before
    assert frontmatter.load(unrelated).content == "Independent change"
    assert index_bodies(tmp_path) == {"affected": "Before", "unrelated": "Independent change"}


def test_failed_index_recovery_still_restores_files_and_identifies_rows(tmp_path, monkeypatch):
    world.initialize_world(tmp_path)
    path = campaign.create_campaign(tmp_path, "affected", "Before")
    search_index.rebuild_index(tmp_path)
    before = path.read_bytes()

    def fail_restore(self):
        raise sqlite3.OperationalError("Index locked during recovery")

    monkeypatch.setattr(Recovery, "_restore_index", fail_restore)
    with pytest.raises(RecoveryError, match="recovery incomplete") as error, Recovery(tmp_path, [path]):
        post = frontmatter.load(path)
        post.content = "Partial change"
        frontmatter_utils.write_post(tmp_path, path, post)
        raise OSError("Original failure")
    assert path.read_bytes() == before
    assert index_bodies(tmp_path)["affected"] == "Partial change"
    assert "affected" in str(error.value) and "index rows" in str(error.value)
