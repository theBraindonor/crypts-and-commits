import json

import pytest
from cac.cli.app import app
from cac.core import campaign, config, rumors, world
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)
    campaign.create_campaign(tmp_path, "c001-work", "Campaign")
    campaign.open_campaign(tmp_path, "c001-work")


def invoke(*args, **kwargs):
    return runner.invoke(app, ["rumors", *args], **kwargs)


def test_commands_literal_output_empty_body_and_confirmation(tmp_path):
    help_result = invoke("--help")
    assert help_result.exit_code == 0
    assert all(name in help_result.output for name in ("list", "get", "create", "update", "delete"))
    text = "[bold]literal[/bold] café 🦉"
    assert invoke("create", "-c", "c001", "--body", text).exit_code == 0
    result = invoke("get")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["body"] == text
    assert text in result.output
    assert json.loads(invoke("list").output)["items"][0]["campaign"] == "c001-work"
    assert invoke("delete", input="n\n").exit_code != 0
    assert rumors.read_body(tmp_path) == text
    assert invoke("update", "--body", "").exit_code == 0
    assert rumors.read_body(tmp_path) == ""
    assert invoke("delete", input="y\n").exit_code == 0
    assert invoke("create", "--body", "New").exit_code == 0
    assert invoke("delete", "--yes").exit_code == 0


@pytest.mark.parametrize("operation", ["create", "update"])
def test_body_file_editor_and_validation(tmp_path, monkeypatch, operation):
    if operation == "update":
        rumors.write(tmp_path, "Initial")
    source = tmp_path / "body file.md"
    text = "---\r\nstatus: raw\r\n---\r\n[tool.ruff] café\r\n\r\n"
    source.write_bytes(text.encode())
    result = invoke(operation, "--body-file", str(source))
    assert result.exit_code == 0, result.output
    assert rumors.read_body(tmp_path) == text
    if operation == "create":
        rumors.delete(tmp_path)
    initial = []
    monkeypatch.setattr("cac.cli.rumors.edit_markdown", lambda body: initial.append(body) or "Edited")
    assert invoke(operation).exit_code == 0
    assert initial == ([text] if operation == "update" else [""])
    if operation == "create":
        rumors.delete(tmp_path)
    for failure in ("conflict", "missing", "directory", "invalid-utf8"):
        source.write_bytes(b"\xff" if failure == "invalid-utf8" else b"New")
        args = [operation, "--body-file", str(source)]
        if failure == "conflict":
            args += ["--body", ""]
        elif failure == "missing":
            args[2] = str(tmp_path / "missing")
        elif failure == "directory":
            args[2] = str(tmp_path)
        assert invoke(*args).exit_code != 0
        if operation == "update":
            assert rumors.read_body(tmp_path) == "Edited"
        else:
            assert rumors.list_documents(tmp_path)["items"] == []


def test_continuation_and_literal_errors(tmp_path, monkeypatch):
    text = "🦉[notes]\r\n" * 150
    rumors.write(tmp_path, text)
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 600)
    chunks, args = [], []
    while True:
        result = invoke("get", *args)
        assert result.exit_code == 0, result.output
        page = json.loads(result.output)
        chunks.append(page["body"])
        if page["next_cursor"] is None:
            break
        args = ["--cursor", page["next_cursor"]]
    assert "".join(chunks) == text
    result = invoke("get", "-c", "[invalid]")
    assert result.exit_code == 1 and "[invalid]" in result.output
    assert invoke("get", "--cursor", "bad").exit_code == 1
