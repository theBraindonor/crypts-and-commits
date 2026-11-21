import json
import re

import pytest
from cac.cli.app import app
from cac.core import campaign, encounter, ruling, world
from typer.testing import CliRunner

runner = CliRunner()
COMMANDS = ("list", "get", "create", "update", "canonize", "note", "reopen", "archive")
NAME = "c002-e001-slugs-unique"


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c002-rulings", "Tactics")
    encounter.create_encounter(tmp_path, "c002-rulings", "e001-core", "Plan")
    campaign.open_campaign(tmp_path, "c002-rulings")


def invoke(*args, **kwargs):
    return runner.invoke(app, ["ruling", *args], **kwargs)


def create(name=NAME, *extra):
    return invoke("create", name, "--body", "Body", "-s", "Summary", "-o", "GM", *extra)


def test_help_lists_exactly_the_eight_commands():
    result = invoke("--help")
    assert result.exit_code == 0
    listed = re.findall(r"^\W ([a-z]+)\s{2,}\S", result.output, re.MULTILINE)
    assert tuple(listed) == COMMANDS


def test_create_requires_summary_and_origin(tmp_path):
    assert invoke("create", NAME, "--body", "Body", "-s", "Summary").exit_code != 0
    assert invoke("create", NAME, "--body", "Body", "-o", "Origin").exit_code != 0
    assert not ruling.ruling_dir(tmp_path).exists()


def test_create_reads_body_file_and_reports_canonical_only_identity(tmp_path):
    source = tmp_path / "ruling body.md"
    source.write_text("From [file]", encoding="utf-8")
    result = invoke("create", NAME, "--body-file", str(source), "-s", "S", "-o", "O")
    assert result.exit_code == 0, result.output
    assert '"short":null,"reason":"canonical_only"' in result.output
    assert ruling.read_metadata(tmp_path, NAME)[1] == "From [file]"


def test_stored_text_with_brackets_prints_intact():
    text = "[tool.pdm] [bold]literal[/bold]"
    assert invoke("create", NAME, "--body", text, "-s", f"S {text}", "-o", f"O {text}").exit_code == 0
    assert invoke("note", NAME, "-m", f"M {text}").exit_code == 0
    shown = invoke("get", NAME)
    assert shown.exit_code == 0, shown.output
    for value in (text, f"S {text}", f"O {text}", f"M {text}"):
        assert value in shown.output


def test_errors_exit_nonzero_and_print_literally():
    create()
    result = invoke("canonize", NAME, "-m", " ")
    assert result.exit_code != 0 and "canonization narrative" in result.output
    result = invoke("list", "--status", "[closed]")
    assert result.exit_code != 0 and "[closed]" in result.output
    result = invoke("get", "c002")
    assert result.exit_code != 0 and "canonical names only" in result.output


def test_paused_campaign_refuses_capture(tmp_path):
    campaign.pause_campaign(tmp_path, "c002-rulings")
    result = create()
    assert result.exit_code != 0 and "rumor" in result.output


def test_end_to_end_walkthrough():
    assert create().exit_code == 0
    assert create("c002-e000-scope").exit_code == 0
    assert invoke("update", NAME, "--body", "Hindsight", "-s", "Updated", "-o", "Review").exit_code == 0
    assert "origin: Review" in invoke("get", NAME).output
    assert invoke("canonize", NAME, "-m", "Added lore x").exit_code == 0
    assert invoke("note", "c002-e000-scope", "-m", "Local detail").exit_code == 0
    assert invoke("reopen", "c002-e000-scope", "-m", "Matters after all").exit_code == 0
    assert invoke("canonize", "c002-e000-scope", "-m", "Updated region").exit_code == 0
    assert invoke("archive", NAME).exit_code == 0
    listed = invoke("list", "--status", "canonized")
    assert json.loads(listed.output.splitlines()[0])["identities"][0]["canonical"] == "c002-e000-scope"
    archived = invoke("list", "--include-archived")
    assert NAME in archived.output and "c002-e000-scope" in archived.output
    assert "archived: True" in invoke("get", NAME).output
