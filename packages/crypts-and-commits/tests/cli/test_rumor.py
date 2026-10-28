import json
import re

import pytest
from cac.cli.app import app
from cac.core import boss, rumor, search_index, world
from typer.testing import CliRunner

runner = CliRunner()
COMMANDS = ("list", "get", "create", "update", "promote", "dismiss", "reopen", "archive", "renumber")


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)


def invoke(*args, **kwargs):
    return runner.invoke(app, ["rumor", *args], **kwargs)


def create(name="r001-idea", *extra):
    return invoke("create", name, "--body", "Body", "-s", "Summary", "-o", "Standup", *extra)


def test_help_lists_exactly_the_nine_commands_and_the_old_group_is_gone():
    result = invoke("--help")
    assert result.exit_code == 0
    # Command rows start right after the panel border; wrapped help lines are indented further.
    listed = re.findall(r"^\W ([a-z]+)\s{2,}\S", result.output, re.MULTILINE)
    assert tuple(listed) == COMMANDS
    old = runner.invoke(app, ["rumors", "list"])
    assert old.exit_code != 0


def test_create_requires_summary_and_origin(tmp_path):
    assert invoke("create", "r001-idea", "--body", "Body", "-s", "Summary").exit_code != 0
    assert invoke("create", "r001-idea", "--body", "Body", "-o", "Origin").exit_code != 0
    assert not rumor.rumor_dir(tmp_path).exists()


def test_create_reads_body_file(tmp_path):
    source = tmp_path / "rumor body.md"
    source.write_text("From [file]", encoding="utf-8")
    assert invoke("create", "r001-idea", "--body-file", str(source), "-s", "S", "-o", "O").exit_code == 0
    assert rumor.read_metadata(tmp_path, "r001-idea")[1] == "From [file]"


def test_stored_text_with_brackets_prints_intact(tmp_path):
    text = "[tool.pdm] [bold]literal[/bold]"
    result = invoke("create", "r001-idea", "--body", text, "-s", f"S {text}", "-o", f"O {text}")
    assert result.exit_code == 0, result.output
    boss.create_boss(tmp_path, "b001-goal", "Goal", "Summary")
    assert invoke("promote", "r001", "b001", "-m", f"M {text}").exit_code == 0
    shown = invoke("get", "r001")
    assert shown.exit_code == 0, shown.output
    for value in (text, f"S {text}", f"O {text}", f"M {text}"):
        assert value in shown.output


def test_errors_exit_nonzero_and_print_literally(tmp_path):
    create()
    result = invoke("dismiss", "r001", "-m", " ")
    assert result.exit_code != 0
    assert "dismissal reason" in result.output
    result = invoke("list", "--status", "[closed]")
    assert result.exit_code != 0
    assert "[closed]" in result.output


def test_end_to_end_walkthrough(tmp_path):
    search_index.rebuild_index(tmp_path)
    assert create("r001-faster-ci").exit_code == 0
    assert create("r001-cache-deps").exit_code == 0

    listed = invoke("list")
    assert listed.exit_code == 0
    assert "r001-cache-deps" in listed.output and "r001-faster-ci" in listed.output

    renumbered = invoke("renumber", "r001-cache-deps", "r002-cache-deps")
    assert renumbered.exit_code == 0, renumbered.output
    assert '"canonical":"r002-cache-deps"' in renumbered.output

    assert (
        invoke("update", "r001-faster-ci", "--body", "Cache wheels", "-s", "Speed up CI", "-o", "Retro").exit_code == 0
    )
    shown = invoke("get", "r001")
    assert "Cache wheels" in shown.output and "origin: Retro" in shown.output

    boss.create_boss(tmp_path, "b001-ci", "Goal", "CI")
    assert invoke("promote", "r001", "b001", "-m", "Fits the CI goal").exit_code == 0
    refused = invoke("renumber", "r001", "r009-faster-ci")
    assert refused.exit_code != 0 and "promoted" in refused.output

    assert invoke("dismiss", "r002", "-m", "Duplicate of r001").exit_code == 0
    assert invoke("reopen", "r002", "-m", "Separate concern").exit_code == 0
    assert invoke("dismiss", "r002", "-m", "Not needed").exit_code == 0
    assert invoke("archive", "r002").exit_code == 0

    assert json.loads(invoke("list", "--status", "promoted").output.splitlines()[0])["identities"][0]["short"] == "r001"
    archived = invoke("list", "--include-archived", "--status", "dismissed")
    assert "r002-cache-deps" in archived.output

    found = runner.invoke(app, ["index", "search", "Retro", "--type", "rumor"])
    assert found.exit_code == 0, found.output
    assert "r001-faster-ci" in found.output
    assert search_index.status(tmp_path)["freshness"] == "fresh"
