from collections.abc import Callable
from pathlib import Path

import pytest
from cac.cli import common as cli_common
from cac.cli.app import app
from cac.core import git_utils
from typer.testing import CliRunner

runner = CliRunner()


def test_get_exposes_legacy_branch_defaults_without_writes(legacy_world: Path) -> None:
    before = legacy_world.read_bytes()

    result = runner.invoke(app, ["world", "get"])

    assert result.exit_code == 0, result.output
    assert "merge_target_branch: main" in result.output
    assert "planning_branch: planning" in result.output
    assert legacy_world.read_bytes() == before


@pytest.mark.parametrize("key", ["merge_target_branch", "planning_branch"])
def test_branch_setting_round_trip_keeps_literal_value(legacy_world: Path, key: str) -> None:
    value = "team/[custom]"
    result = runner.invoke(app, ["world", "set", key, value])

    assert result.exit_code == 0, result.output
    assert f"Set {key} = {value}" in result.output
    result = runner.invoke(app, ["world", "get"])
    assert result.exit_code == 0, result.output
    assert f"{key}: {value}" in result.output


def test_body_file_crlf_matches_inline_input(tmp_path: Path, seed_world: Callable[[], None]) -> None:
    from cac.core import world

    seed_world()
    body = "# World\r\n\r\nCafé → [tool.pdm.workspace]\r\n"
    source = tmp_path / "world body.md"
    source.write_bytes(body.encode("utf-8"))
    result = runner.invoke(app, ["world", "set-body", "--body", body])
    assert result.exit_code == 0
    inline = world.read_world(tmp_path).body

    result = runner.invoke(app, ["world", "set-body", "--body-file", str(source)])

    assert result.exit_code == 0, result.output
    assert world.read_world(tmp_path).body == inline
    assert source.read_bytes() == body.encode("utf-8")


def _break_git_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(root: Path) -> str:
        raise git_utils.GitIdentityError("git user.name is not configured.")

    monkeypatch.setattr(git_utils, "current_git_user", _raise)


def test_get_missing_world_fails() -> None:
    result = runner.invoke(app, ["world", "get"])

    assert result.exit_code == 1


def test_get_shows_metadata_and_body(seed_world: Callable[[], None]) -> None:
    seed_world()

    result = runner.invoke(app, ["world", "get"])

    assert result.exit_code == 0
    assert "name" in result.output
    assert "Be sure to edit this world definition file before starting development!" in result.output


def test_get_preserves_bracketed_body_text(tmp_path: Path, seed_world: Callable[[], None]) -> None:
    seed_world()
    runner.invoke(app, ["world", "set-body", "--body", "See [tool.pdm.workspace] for details."])

    result = runner.invoke(app, ["world", "get"])

    assert result.exit_code == 0
    assert "[tool.pdm.workspace]" in result.output


def test_set_updates_frontmatter_attribute(tmp_path: Path, seed_world: Callable[[], None]) -> None:
    seed_world()

    result = runner.invoke(app, ["world", "set", "name", "my-project"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "world.md").read_text(encoding="utf-8")
    assert "name: my-project" in text


def test_set_missing_world_fails() -> None:
    result = runner.invoke(app, ["world", "set", "name", "my-project"])

    assert result.exit_code == 1


def test_set_fails_when_git_identity_unresolvable(
    monkeypatch: pytest.MonkeyPatch, seed_world: Callable[[], None]
) -> None:
    seed_world()
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["world", "set", "name", "my-project"])

    assert result.exit_code == 1


def test_set_body_with_body_option(tmp_path: Path, seed_world: Callable[[], None]) -> None:
    seed_world()

    result = runner.invoke(app, ["world", "set-body", "--body", "New content."])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "world.md").read_text(encoding="utf-8")
    assert "New content." in text
    assert "This world has not been described yet." not in text


def test_set_body_opens_editor_when_body_omitted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, seed_world: Callable[[], None]
) -> None:
    seed_world()
    monkeypatch.setattr(cli_common.click, "edit", lambda *_args, **_kwargs: "Edited content.")

    result = runner.invoke(app, ["world", "set-body"])

    assert result.exit_code == 0
    text = (tmp_path / ".sourcebook" / "world.md").read_text(encoding="utf-8")
    assert "Edited content." in text


def test_set_body_missing_world_fails() -> None:
    result = runner.invoke(app, ["world", "set-body", "--body", "text"])

    assert result.exit_code == 1


def test_set_body_fails_when_git_identity_unresolvable(
    monkeypatch: pytest.MonkeyPatch, seed_world: Callable[[], None]
) -> None:
    seed_world()
    _break_git_identity(monkeypatch)

    result = runner.invoke(app, ["world", "set-body", "--body", "text"])

    assert result.exit_code == 1


def test_get_from_a_subdirectory_finds_the_root_sourcebook(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, seed_world: Callable[[], None]
) -> None:
    seed_world()
    nested = tmp_path / "packages" / "crypts-and-commits"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    result = runner.invoke(app, ["world", "get"])

    assert result.exit_code == 0
    assert "name" in result.output
    assert not (nested / ".sourcebook").exists()


def test_get_truncates_body_over_budget(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, seed_world: Callable[[], None]
) -> None:
    seed_world()
    runner.invoke(app, ["world", "set-body", "--body", "x" * 2000])
    monkeypatch.setattr("cac.core.config.RESPONSE_BUDGET", 800)

    result = runner.invoke(app, ["world", "get"])

    assert result.exit_code == 0
    assert "[TRUNCATED" in result.output and "next_cursor: " in result.output
    assert ".sourcebook" not in result.output
